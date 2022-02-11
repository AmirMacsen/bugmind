from django.urls import re_path, include
from . import views
from . import manage
from management.views import issues

app_name = "projects"

urlpatterns = [
    re_path(r"^list/$", views.project_list, name="project_list"),
    # project_type 区分是我创建的项目还是我参与的项目
    re_path(r"^star/(?P<project_type>\w+)/(?P<project_id>\d+)/$", views.project_star, name="project_star"),
    re_path(r"^unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$", views.project_unstar, name="project_unstar"),

    re_path(r'^manage/(?P<project_id>\d+)/', include('management.urls', namespace="management")),

    # 邀请用户
    re_path(r"^issues/invite/join/(?P<code>\w+)/$", issues.invite_join, name="invite_join"),
]
