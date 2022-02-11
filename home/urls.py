from django.urls import re_path
from . import views

app_name = "home"

urlpatterns = [
    re_path(r"^price/$", views.price, name="price"),
    re_path(r"^payment/(?P<policy_id>\d+)/$", views.payment, name="payment"),
    re_path(r"^pay/$", views.pay, name="pay"),
    re_path(r"^pay/notify/$", views.pay_notify, name="pay_notify"),
    re_path(r"^404/$", views.error_404, name="error_404"),
    re_path(r"", views.index, name="index"),
]