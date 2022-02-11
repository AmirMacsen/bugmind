import time

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse

from accounts.decorators import login_required
from management.models import IssuesType
from .forms import ProjectModelForm
from .models import Project, ProjectUser
from utils.tencent import cos


@login_required
def project_list(request):
    if request.method == "GET":
        form = ProjectModelForm(request)
        # 查询项目列表  1.星标项目 2.我参与的项目 3.我创建的项目
        project_dict = {'star_projects': [], "participant_projects": [], "created_projects": []}
        user = request.tracer.user
        projects = Project.objects.filter(creator=user)
        for row in projects:
            if row.star:
                project_dict['star_projects'].append({"value": row, "type": "owner"})
            else:
                project_dict['created_projects'].append(row)
        participant_projects = ProjectUser.objects.filter(user=request.tracer.user)
        for item in participant_projects:
            if item.star:
                project_dict['star_projects'].append({"value": item.project, "type": "participant"})
            else:
                project_dict['participant_projects'].append(item.project)
        return render(request, 'projects/project_list.html', {"form": form, "project_dict": project_dict})
    form = ProjectModelForm(request, request.POST)

    if form.is_valid():
        # 为项目创建一个桶和区域
        bucket = "bugmind-{}-{}-1302735599".format(request.tracer.user.mobile_phone, str(int(time.time())))
        region = "ap-guangzhou"
        cos.create_bucket(bucket, region)
        # 创建项目
        form.instance.region = region
        form.instance.bucket = bucket
        form.instance.creator = request.tracer.user
        instance = form.save()
        # 给项目初始化问题类型
        issues_type_obj_list = []
        for item in IssuesType.PROJECT_INIT_LIST:
            issues_type_obj_list.append(IssuesType(project=instance, title=item))
        IssuesType.objects.bulk_create(issues_type_obj_list)
        return JsonResponse({"status": True, })

    return JsonResponse({"status": False, "error": form.errors})


@login_required
def project_star(request, project_type, project_id):
    if project_type == "my":
        Project.objects.filter(creator=request.tracer.user, id=project_id).update(star=True)
        return redirect('projects:project_list')
    if project_type == "participant":
        ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=True)
        return redirect('projects:project_list')

    return HttpResponse("请求错误")


@login_required
def project_unstar(request, project_type, project_id):
    if project_type == "owner":
        Project.objects.filter(creator=request.tracer.user, id=project_id).update(star=False)
        return redirect('projects:project_list')
    if project_type == "participant":
        ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=False)
        return redirect('projects:project_list')

    return HttpResponse("请求错误")
