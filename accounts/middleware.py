import datetime

from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from .models import UserInfo
from pricepolicy.models import Transaction


class Tracer:
    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """如果用户已经登录，则在request中赋值"""
        request.tracer = Tracer()
        user_id = request.session.get('user_id')
        request.tracer.user = UserInfo.objects.filter(id=user_id).first()

        # 白名单实现用户鉴权，本次采用的是装饰器实现，以下可以使用
        # current_path = request.path_info
        # if current_path in settings.WHITE_REGEX_URL_LIST:
        #     return
        #
        # if not request.tracer:
        #     return redirect("accounts:login")

        if request.tracer.user:
            # 查询用户套餐
            # 获取用户最近的交易记录,只查询已支付的
            _object = Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-id').first()
            # 判断对象是否已经过期
            current_datetime = datetime.datetime.now()
            if _object.end_datetime and _object.end_datetime < current_datetime:
                # 过期
                _object = Transaction.objects.filter(user=request.tracer.user, status=2, price_policy__category=1) \
                    .order_by('id').first()
            request.tracer.price_policy = _object
