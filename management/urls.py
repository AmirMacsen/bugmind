from django.urls import re_path, include
from .views import views, wiki, file, settings, issues, dashboard, statistics

app_name = "management"

urlpatterns = [
    # 项目管理
    re_path(r"^dashboard/$", dashboard.dashboard, name="dashboard"),
    re_path(r"^dashboard/issues/chart/$", dashboard.dashboard_chart, name="dashboard_chart"),

    re_path(r"^statistics/$", statistics.statistics, name="statistics"),
    re_path(r"^statistics/priority/$", statistics.statistics_priority, name="statistics_priority"),
    re_path(r"^statistics/project/user/$", statistics.project_user, name="statistics_project_user"),

    re_path(r"^wiki/$", wiki.wiki, name="wiki"),
    re_path(r"^wiki/add/$", wiki.wiki_add, name="wiki_add"),
    re_path(r"^wiki/catalog/$", wiki.wiki_catalog, name="wiki_catalog"),
    re_path(r"^wiki/delete/(?P<wiki_id>\d+)/$", wiki.wiki_delete, name="wiki_delete"),
    re_path(r"^wiki/edit/(?P<wiki_id>\d+)/$", wiki.wiki_edit, name="wiki_edit"),
    re_path(r"^wiki/upload/$", wiki.wiki_upload, name="wiki_upload"),

    re_path(r"^file/$", file.file, name="file"),
    re_path(r"^file/delete/$", file.file_delete, name="file_delete"),
    re_path(r'^cos/credential/$', file.cos_credential, name='cos_credential'),
    re_path(r'^file/post/$', file.file_post, name='file_post'),
    re_path(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),

    re_path(r"^setting/$", settings.setting, name="setting"),
    re_path(r"^setting/delete/$", settings.setting_delete, name="setting_delete"),

    re_path(r"^issues/$", issues.issues, name="issues"),
    re_path(r"^issues/detail/(?P<issues_id>\d+)/$", issues.issues_detail, name="issues_detail"),
    re_path(r"^issues/record/(?P<issues_id>\d+)/$", issues.issues_record, name="issues_record"),
    re_path(r"^issues/change/(?P<issues_id>\d+)/$", issues.issues_change, name="issues_change"),
    re_path(r"^issues/invite/url/$", issues.invite_url, name="invite_url"),

]
