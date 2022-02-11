import datetime
import uuid
from io import BytesIO

from django.core import serializers
from django.db.models import Q
from django.db import transaction, DatabaseError
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect

from accounts.forms import RegisterForm, SendSmsForm, LoginSmsForm, LoginForm
from pricepolicy.models import Transaction, PricePolicy
from utils.image.verification_code import check_code
from .models import UserInfo


def logout(request):
    request.session.flush()
    return redirect('/index')


def login(request):
    """
    用户名密码登录
    """
    if request.method == "GET":
        form = LoginForm(request)
        return render(request, "accounts/account/login.html", {"form": form})

    form = LoginForm(request, request.POST)
    if form.is_valid():
        # 用户名密码校验
        loginName = form.cleaned_data['loginName']
        password = form.cleaned_data['password']
        user = UserInfo.objects.filter(Q(email=loginName) | Q(mobile_phone=loginName)).filter(
            password=password
        ).first()
        if user:
            request.session['user_id'] = user.id
            request.session.set_expiry(60*60*2)
            return redirect("/index")
        form.add_error('loginName', "输入错误，请重新输入")

    return render(request, 'accounts/account/login.html', {"form": form})


def image_code(request):
    """
    生成图片验证码
    """
    image, code = check_code()
    request.session['image_code'] = code
    request.session.set_expiry(60)
    stream = BytesIO()
    image.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def log_sms(request):
    if request.method == "GET":
        form = LoginSmsForm()
        return render(request,
                      "accounts/account/login_sms.html",
                      {"form": form})
    form = LoginSmsForm(request.POST)
    if form.is_valid():
        # 用户输入正确
        user = form.cleaned_data['mobile_phone']
        # todo 用户信息放入session, 需要序列化的相关知识
        request.session['user_id'] = user.id
        request.session.set_expiry(60*60*2)
        return JsonResponse({"status": True, "data": "/index"})

    return JsonResponse({"status": False, "error": form.errors})


def register(request):
    """ 注册 """
    if request.method == "GET":
        form = RegisterForm()
        return render(request, "accounts/account/register.html", {"form": form})

    form = RegisterForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            try:
                instance = form.save()
                # 创建交易记录
                price_policy = PricePolicy.objects.filter(category=1, title="个人免费版").first()
                Transaction.objects.create(
                    status=2,
                    order=str(uuid.uuid4()),
                    user=instance,
                    price_policy=price_policy,
                    count=0,
                    price=0,
                    start_datetime=datetime.datetime.now(),
                )
            except DatabaseError:
                return JsonResponse({"status": False, 'db_error': "服务端异常"})

        return JsonResponse({"status": True, 'data': "/accounts/loginsms"})

    return JsonResponse({"status": False, 'error': form.errors})


def send_sms(request):
    if request.method == "GET":
        # 校验表单
        form = SendSmsForm(request, data=request.GET)
        if form.is_valid():
            return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'error': form.errors})
