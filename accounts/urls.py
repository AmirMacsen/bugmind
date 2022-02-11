from django.urls import re_path,path
from . import views

app_name = "accounts"

urlpatterns = [
    re_path(r'^register/$', views.register, name="register"),
    re_path(r'^send/sms/$', views.send_sms, name="send_sms"),
    re_path(r'^loginsms/$', views.log_sms, name="login_sms"),
    re_path(r'^login/$', views.login, name="login"),
    re_path(r'^logout/$', views.logout, name="logout"),
    re_path(r'^imagecode/$', views.image_code, name="image_code"),
]
