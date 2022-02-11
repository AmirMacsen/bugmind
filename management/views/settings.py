from django.http import JsonResponse
from django.shortcuts import render, redirect

from accounts.decorators import login_required
from projects.models import Project

from utils.tencent.cos import delete_bucket


@login_required
def setting(request, project_id):
    return render(request, "management/setting.html")


@login_required
def setting_delete(request, project_id):
    """删除项目"""
    if request.method == "GET":
        return render(request, "management/setting_delete.html")

    project_name = request.POST.get("project_name")

    project_obj = Project.objects.filter(id=project_id, creator=request.tracer.user).first()
    if not project_obj or project_name != project_obj.name:
        return render(request, "management/setting_delete.html", {"error": "项目名不存在或不是项目的创建者"})

    # 1.删除桶
    #       - 删除桶中的所有文件
    #       - 删除桶中的所有碎片
    #       - 删除桶
    delete_bucket(request.tracer.project.bucket, request.tracer.project.region)
    # 2.删除项目
    Project.objects.filter(id=request.tracer.project.id).delete()

    return redirect("projects:project_list")


