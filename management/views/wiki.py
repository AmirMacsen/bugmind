from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

from accounts.decorators import login_required
from management.forms.wiki import WikiAddForm
from management.models import Wiki
from utils.encrypt.md5 import uid
from utils.tencent.cos import upload_file_from_buffer


@login_required
def wiki(request, project_id):
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, "management/wiki/wiki.html")
    wiki_obj = Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    return render(request, "management/wiki/wiki.html", {"wiki_obj": wiki_obj})


@login_required
def wiki_add(request, project_id):
    if request.method == "GET":
        form = WikiAddForm(project_id)
        return render(request, 'management/wiki/wiki_form.html', {"form": form})
    form = WikiAddForm(project_id=project_id, data=request.POST)
    if form.is_valid():
        # 判断用户是否选择了父文章
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse("projects:management:wiki", kwargs={'project_id': project_id})
        return redirect(url)
    return render(request, 'management/wiki/wiki_form.html', {"form": form})


@login_required
def wiki_catalog(request, project_id):
    if request.method == "GET":
        data_list = Wiki.objects.filter(project_id=project_id).values("id", 'title', 'parent_id').order_by("depth",
                                                                                                           "id")
        print(data_list)
        return JsonResponse({"status": True, "data": list(data_list)})


@login_required
def wiki_delete(request, project_id, wiki_id):
    """删除wiki"""
    Wiki.objects.filter(project_id=project_id, id=wiki_id).delete()
    url = reverse("projects:management:wiki", kwargs={'project_id': project_id})
    return redirect(url)


@login_required
def wiki_edit(request, project_id, wiki_id):
    """编辑wiki"""
    wiki_obj = Wiki.objects.filter(project_id=project_id, id=wiki_id).first()
    if not wiki_obj:
        url = reverse("projects:management:wiki", kwargs={'project_id': project_id})
        return redirect(url)
    if request.method == "GET":
        form = WikiAddForm(project_id, wiki_id=wiki_id, instance=wiki_obj)
        return render(request, "management/wiki/wiki_form.html", {"form": form})
    form = WikiAddForm(project_id, data=request.POST, instance=wiki_obj, )
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.save()
        url = reverse("projects:management:wiki", kwargs={'project_id': project_id})
        preview_url = "{0}?wiki_id={1}".format(url, wiki_id)
        return redirect(preview_url)
    return render(request, "management/wiki/wiki_form.html", {"form": form})


@login_required
@xframe_options_exempt
@csrf_exempt
def wiki_upload(request, project_id):
    """
    markdown上传图片
    :param request:
    :return:
    """
    result = {
        "success": 0,
        "message": None,
        "url": None
    }
    image_obj = request.FILES.get("editormd-image-file")
    if not image_obj:
        result['message'] = "请上传符合格式的图片"
        return JsonResponse(result)
    etx = image_obj.name.rsplit('.')[-1]
    key = f"{uid(request.tracer.user.mobile_phone)}.{etx}"
    # 将图片对象上传到当前项目的桶中
    image_url = upload_file_from_buffer(image_obj, key, request.tracer.project.bucket, request.tracer.project.region)
    result['success'] = 1
    result['url'] = image_url
    return JsonResponse(result)
