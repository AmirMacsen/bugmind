from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from accounts.decorators import login_required
from projects.models import Project, ProjectUser


class CheckProjectsViewMiddleware(MiddlewareMixin):
    """
    该中间件用于检测用户访问项目详情是否具有权限
    1.url是否start_with  projects/management/
    2.project_id是否是自己可以查看的
    Tips：process_view是进行路由匹配进入视图函数之前运行的
    """
    def process_view(self, request, view, args, kwargs):
        # 判断url
        if not request.path_info.startswith("/projects/manage/"):
            return
        # 是否是我创建的项目或者我参与的项目
        project_id = kwargs.get("project_id")
        user = request.tracer.user
        if not user:
            return redirect("accounts:login")

        project_obj = Project.objects.filter(
            creator=user,
            id=project_id
        ).first()

        if project_obj:
            request.tracer.project = project_obj
            return
        project_user_obj = ProjectUser.objects.filter(
            user=user,
            project_id=project_id
        ).first()
        if project_user_obj:
            request.tracer.project = project_user_obj.project
            return

        return redirect("home:error_404")