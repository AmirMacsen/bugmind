import json

import requests
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from accounts.decorators import login_required
from management.forms.file import NewFolderModelForm, FileModelForm
from management.models import File

from utils.tencent.cos import delete_file, delete_file_list, credential


@login_required
def file(request, project_id):
    """文件列表 & 添加文件夹"""
    parent_obj = None
    folder_id = request.GET.get("folder", "")
    if folder_id.isdecimal():
        parent_obj = File.objects.filter(file_type=1, project=request.tracer.project, id=int(folder_id)).first()

    if request.method == "GET":
        breadcrumb_list = []
        parent = parent_obj
        while parent:
            # breadcrumb_list.insert(0, {"id":parent.id, "name":parent.name})
            breadcrumb_list.insert(0, model_to_dict(parent, ['id', 'name']))
            parent = parent.parent
        # 查看当前目录下所有的文件以及文件夹
        qs = File.objects.filter(project=request.tracer.project)
        if parent_obj:
            # 说明已经进入了目录
            file_obj_list = qs.filter(parent=parent_obj).order_by('file_type')
        else:
            file_obj_list = qs.filter(parent__isnull=True)
        form = NewFolderModelForm(request, parent_obj)
        context = {
            "form": form,
            "file_obj_list": file_obj_list,
            "breadcrumb_list": breadcrumb_list,
            "folder_obj": parent_obj
        }
        return render(request, "management/file.html", context)

    # ADD FOLDER or update folder
    fid = request.POST.get("fid", "")
    edit_obj = None
    if fid.isdecimal():
        edit_obj = File.objects.filter(id=int(fid), file_type=1, project=request.tracer.project).first()
    if edit_obj:
        form = NewFolderModelForm(request=request, parent_obj=parent_obj, data=request.POST, instance=edit_obj)
    else:
        form = NewFolderModelForm(request=request, parent_obj=parent_obj, data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.file_type = 1
        form.instance.updator = request.tracer.user
        form.instance.parent = parent_obj
        form.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})


@login_required
def file_delete(request, project_id):
    """删除文件"""
    fid = request.GET.get("fid")
    # 删除了文件或者文件夹，支持级联删除
    delete_obj = File.objects.filter(id=fid, project=request.tracer.project).first()
    if delete_obj.file_type == "1":
        # 删除文件夹
        total_size = 0
        key_list = []
        folder_list = [delete_obj, ]
        for folder in folder_list:
            child_list = File.objects.filter(project=request.tracer.project, parent=folder).order_by('file_type')
            for child in child_list:
                if child.file_type == "1":
                    folder_list.append(child)
                else:
                    # 如果是文件则需要从cos中删除删除
                    # 1.文件大小汇总，用以归还用户的可使用空间大小；2.调用cos的接口批量删除文件
                    total_size += child.size
                    key_list.append({"Key": delete_file})

        if key_list:
            delete_file_list(key_list, request.tracer.project.bucket, request.tracer.project.region)
        if total_size:
            request.tracer.project.use_space -= total_size
            request.tracer.project.save()

        delete_obj.delete()
    else:
        # 删除文件
        # 归还使用空间
        request.tracer.project.use_space -= delete_obj.size
        request.tracer.project.save()

        # 在cos中删除文件
        delete_file(key=delete_obj.key, bucket=request.tracer.project.bucket, region=request.tracer.project.region)
        # 在数据库中删除当前的文件
        delete_obj.delete()
        return JsonResponse({"status": True})


@csrf_exempt
@login_required
def cos_credential(request, project_id):
    """获取cos上传的临时凭证"""
    # 做容量限制：单文件 & 总容量
    file_list = json.loads(request.body.decode("utf-8"))
    total_size = 0
    for item in file_list:
        # 获取单文件限制
        per_file_size_limit = request.tracer.price_policy.price_policy.per_file_size * 1024 * 1024
        if item['size'] > per_file_size_limit:
            msg = "单文件超出限制(最大{}M，文件: {} )".format(
                request.tracer.price_policy.price_policy.per_file_size, item['size']
            )
            return JsonResponse({"status": False, "error": msg})
        total_size += item['size']
    # 获取项目容许的总容量
    project_space = request.tracer.price_policy.price_policy.project_space
    use_space = request.tracer.project.use_space
    if use_space + total_size > project_space * 1024 * 1024:
        return JsonResponse({"status": False, "error": "容量超过限制，请升级套餐"})
    print(total_size)
    data_dict = credential(request.tracer.project.bucket, request.tracer.project.region)
    return JsonResponse({"status": True, "data": data_dict})


@csrf_exempt
@login_required
def file_post(request, project_id):
    """上传成功的文件写入到数据库"""
    """
    "name": file_name,
    "size": file_size,
    "key": key,
    "parent": CURRENT_FOLDER_ID,
    "etag": data.ETag,
    "file_path": data.Location
    """

    # 拿到etag，通过key再去cos获取文件，校验etag是否一致
    form = FileModelForm(request, data=request.POST)
    if form.is_valid():
        # form.instance.file_type = 2
        # form.instance.updator = request.tracer.user
        # instance = form.save()
        data_dict = form.cleaned_data
        data_dict.pop("etag")
        data_dict.update({"project": request.tracer.project, 'file_type': 2, "updator": request.tracer.user})

        instance = File.objects.create(**data_dict)

        # 项目的已使用空间：更新
        request.tracer.project.use_space += data_dict['size']
        request.tracer.project.save()

        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.size,
            'updator': instance.updator.username,
            'update_datetime': instance.update_datetime.strftime("%Y年%m月%d %H:%M"),
            'file_type': instance.get_file_type_display(),
            'download_url': reverse("projects:management:file_download",
                                    kwargs={"project_id": request.tracer.project.id,
                                            "file_id": instance.id})
        }
        return JsonResponse({"status": True, "data": result})

    return JsonResponse({"status": False, "error": "文件错误"})


@login_required
def file_download(request, project_id, file_id):
    file_object = File.objects.filter(id=file_id, project_id=project_id).first()
    res = requests.get(file_object.path)

    data = res.iter_content()

    response = HttpResponse(data, content_type="application/octet-stream")
    from django.utils.encoding import escape_uri_path

    response['Content-Disposition'] = "attachment; filename={};".format(escape_uri_path(file_object.name))
    return response