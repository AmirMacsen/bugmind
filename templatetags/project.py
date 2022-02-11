from django.template import Library
from django.shortcuts import reverse

from projects.models import Project, ProjectUser

register = Library()


@register.inclusion_tag("inclusion/all_project_list.html")
def all_project_list(request):
    # 获取创建的项目
    # 获取参与的项目
    project_list = Project.objects.filter(creator=request.tracer.user)
    participant_projects = ProjectUser.objects.filter(user=request.tracer.user)
    return {"owner": project_list, "participant": participant_projects}


@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data_list = [
        {'title': '概览', 'url': reverse("projects:management:dashboard", kwargs={"project_id": request.tracer.project.id})},
        {'title': '问题', 'url': reverse("projects:management:issues", kwargs={"project_id": request.tracer.project.id})},
        {'title': '统计', 'url': reverse("projects:management:statistics", kwargs={"project_id": request.tracer.project.id})},
        {'title': 'wiki', 'url': reverse("projects:management:wiki", kwargs={"project_id": request.tracer.project.id})},
        {'title': '文件', 'url': reverse("projects:management:file", kwargs={"project_id": request.tracer.project.id})},
        {'title': '配置', 'url': reverse("projects:management:setting", kwargs={"project_id": request.tracer.project.id})},
    ]
    for item in data_list:
        if request.path_info.startswith(item['url']):
            item['class'] = 'active'
    return {'data_list': data_list}
