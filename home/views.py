import datetime
import decimal
import json
from typing import Any

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.cache import cache

from accounts.decorators import login_required
from pricepolicy import models
from pricepolicy.models import Transaction
from utils.encrypt.md5 import uid
from utils.alibaba.alipay import AliPay


class DecimalEncoder(json.JSONEncoder):
    """Decimal序列化工具"""

    def default(self, o: Any) -> Any:
        if isinstance(o, decimal.Decimal):
            return float(o)
        super().default(o)


def index(request):
    """首页"""
    return render(request, "home/index.html")


def error_404(request):
    """首页"""
    return render(request, "error/404.html")


def price(request):
    """价格页面"""
    # 获取套餐
    policy_list = models.PricePolicy.objects.filter(category=2)
    return render(request, "home/price.html", {"policy_list": policy_list})


@login_required
def payment(request, policy_id):
    """支付页面"""
    # 获取价格策略
    policy = models.PricePolicy.objects.filter(id=policy_id, category=2).first()
    if not policy:
        return redirect('home:price')
    # 获取数量
    number = request.GET.get('number', '')
    if not number or not number.isdecimal():
        return redirect('home:price')
    number = int(number)
    if number < 1:
        return redirect("home:price")

    # 计算原价
    origin_price = number * policy.price

    # 之前购买过套餐
    balance = 0
    _object = None
    if request.tracer.price_policy.price_policy.category == 2:
        # 找到之前的订单  总支付的费用 、 开始-结束时间、 剩余天数 = 抵扣的钱
        _object = Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-id').first()
        total_timedelta = _object.end_datetime - _object.start_datetime
        balance_timedelta = _object.end_datetime - datetime.datetime.now()
        if total_timedelta.days == balance_timedelta.days:
            balance = _object.price / total_timedelta.days * (balance_timedelta.days - 1)
        else:
            balance = _object.price / total_timedelta.days * balance_timedelta.days

    if balance >= origin_price:
        return redirect('home:price')

    context = {
        'policy_id': policy.id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance, 2),
        'total_price': origin_price - round(balance, 2)
    }
    key = "payment_{}".format(request.tracer.user.mobile_phone)
    cache.set(key, json.dumps(context, cls=DecimalEncoder), 60 * 30)
    context['policy_object'] = policy
    context['transaction'] = _object
    return render(request, 'home/payment.html', context)


@login_required
def pay(request):
    """生成订单 去支付宝支付"""
    # 需要对用户提交的数据再次进行校验
    key = "payment_{}".format(request.tracer.user.mobile_phone)
    context_string = cache.get(key)
    if not context_string:
        return redirect('home:price')

    context = json.loads(context_string)

    # 生成交易记录
    order_id = uid(request.tracer.user.mobile_phone)
    Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=context['total_price'],
    )
    # 跳转到支付宝支付
    #      - 生成支付宝的链接
    #      - 跳转到这个链接
    total_price = context['total_price']
    # params = {
    #     'app_id': "2021000119611759",
    #     'method': 'alipay.trade.page.pay',
    #     'format': 'JSON',
    #     'return_url': "http://127.0.0.1:8001/pay/notify/",
    #     'notify_url': "http://127.0.0.1:8001/pay/notify/",
    #     'charset': 'utf-8',
    #     'sign_type': 'RSA2',
    #     'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     'version': '1.0',
    #     'biz_content': json.dumps({
    #         'out_trade_no': order_id,
    #         'product_code': 'FAST_INSTANT_TRADE_PAY',
    #         'total_amount': total_price,
    #         'subject': "tracer payment"
    #     }, separators=(',', ':'))
    # }
    #
    # # 获取待签名的字符串
    # unsigned_string = "&".join(["{0}={1}".format(k, params[k]) for k in sorted(params)])
    #
    # # 签名 SHA256WithRSA(对应sign_type为RSA2)
    # from Crypto.PublicKey import RSA
    # from Crypto.Signature import PKCS1_v1_5
    # from Crypto.Hash import SHA256
    # from base64 import decodebytes, encodebytes
    #
    # # SHA256WithRSA + 应用私钥 对待签名的字符串 进行签名
    # private_key = RSA.importKey(open("files/应用私钥.txt").read())
    # signer = PKCS1_v1_5.new(private_key)
    # signature = signer.sign(SHA256.new(unsigned_string.encode('utf-8')))
    #
    # # 对签名之后的执行进行base64 编码，转换为字符串
    # sign_string = encodebytes(signature).decode("utf8").replace('\n', '')
    #
    # # 把生成的签名赋值给sign参数，拼接到请求参数中。
    #
    # from urllib.parse import quote_plus
    # result = "&".join(["{0}={1}".format(k, quote_plus(params[k])) for k in sorted(params)])
    # result = result + "&sign=" + quote_plus(sign_string)
    #
    # gateway = "https://openapi.alipaydev.com/gateway.do"
    # ali_pay_url = "{}?{}".format(gateway, result)
    #
    # return redirect(ali_pay_url)

    alipay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = alipay.direct_pay(
        subject="BugMind系统会员",
        out_trade_no=order_id,
        total_amount=total_price
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)


def pay_notify(request):
    """ 支付成功之后触发的URL """
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    if request.method == 'GET':
        # 只做跳转，判断是否支付成功了，不做订单的状态更新。
        # 支付吧会讲订单号返回：获取订单ID，然后根据订单ID做状态更新 + 认证。
        # 支付宝公钥对支付给我返回的数据request.GET 进行检查，通过则表示这是支付宝返还的接口。
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = ali_pay.verify(params, sign)
        if status:
            """
            current_datetime = datetime.datetime.now()
            out_trade_no = params['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()

            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
            _object.save()
            """
            return HttpResponse('支付完成')
        return HttpResponse('支付失败')
    else:
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()

            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return HttpResponse('success')

        return HttpResponse('error')
