import random

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from accounts.models import UserInfo
from utils.encrypt import md5


class BootStrapForm(object):
    bootstrap_exclude_field = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_exclude_field:
                continue
            field.widget.attrs['class'] = "form-control"
            field.widget.attrs['placeholder'] = f"请输入{field.label}"


class LoginForm(BootStrapForm, forms.Form):
    loginName = forms.CharField(label="手机号或邮箱")
    password = forms.CharField(label="密码",
                               widget=forms.PasswordInput(render_value=True),
                               )
    code = forms.CharField(label="图片验证码")

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data.get("password", 0)
        if not pwd:
            raise ValidationError("请输入密码")
        return md5.md5(pwd)

    def clean_code(self):
        """验证码验证"""
        code = self.cleaned_data.get("code")
        session_code = self.request.session.get("image_code")
        if not session_code:
            raise ValidationError("验证码已经过期")

        if code.strip().upper() != session_code.strip().upper():
            raise ValidationError("验证码输入错误")

        return code


class LoginSmsForm(BootStrapForm, forms.Form):
    mobile_phone = forms.CharField(label="手机号",
                                   validators=[
                                       RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', "手机号格式错误"), ])

    code = forms.CharField(label="验证码", widget=forms.TextInput())

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data.get("mobile_phone")
        user = UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        if not user:
            raise ValidationError("手机号不存在")
        return user

    def clean_code(self):
        user = self.cleaned_data.get("mobile_phone")
        code = self.cleaned_data.get("code")

        if not user:
            return code

        redis_code = cache.get(user.mobile_phone)
        if not redis_code or code.strip() != str(redis_code):
            raise ValidationError("验证码失效或者未发送")
        return code


class RegisterForm(BootStrapForm, forms.ModelForm):
    mobile_phone = forms.CharField(label="手机号",
                                   validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', "手机号格式错误"), ])
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(),
        min_length=8,
        max_length=64,
        error_messages={
            'min_length': "密码长度不能小于8*******8个字符",
            'max_length': "密码长度不能大于64个字符"
        })
    confirm = forms.CharField(
        label="重复密码",
        widget=forms.PasswordInput(),
        min_length=8,
        max_length=64,
        error_messages={
            'min_length': "密码长度不能小于8个字符",
            'max_length': "密码长度不能大于64个字符"
        })
    code = forms.CharField(label="验证码", widget=forms.TextInput())

    class Meta:
        model = UserInfo
        fields = ['username', 'email', 'password', 'confirm', 'mobile_phone', 'code']

    def clean_username(self):
        username = self.cleaned_data['username']

        if UserInfo.objects.filter(username=username).exists():
            raise ValidationError("用户名已经存在")

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if UserInfo.objects.filter(email=email).exists():
            raise ValidationError("邮箱已经存在")
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return md5.md5(pwd)

    def clean_confirm(self):
        pwd = self.cleaned_data.get('password')
        confirm = md5.md5(self.cleaned_data['confirm'])

        if pwd != confirm:
            raise ValidationError("两次密码不一致")
        return confirm

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']

        if UserInfo.objects.filter(mobile_phone=mobile_phone).exists():
            raise ValidationError("手机号已经存在")
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code

        redis_code = cache.get(mobile_phone)
        if not redis_code or code.strip() != str(redis_code):
            raise ValidationError("验证码失效或者未发送")
        return code


class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label="手机号",
                                   validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', "手机号格式错误"), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        # 判断短信模板是否有问题
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE[tpl]
        if not template_id:
            raise ValidationError("短信模板错误")

        if tpl == "login":
            # 校验手机号是否存在
            if not UserInfo.objects.filter(mobile_phone=mobile_phone).exists():
                raise ValidationError("手机号不存在")
        else:
            # 校验手机号的唯一性
            if UserInfo.objects.filter(mobile_phone=mobile_phone).exists():
                raise ValidationError("手机号已经存在")

        # 发短信 & 写入redis
        code = random.randrange(1000, 9999)
        # todo 发短信的逻辑
        # sms = send_sms_single()
        # if sms['result'] !=0:
        #     raise ValidationError("短信发送失败",f" {sms['error']}")
        # 写入redis
        cache.set(mobile_phone, code, 300)
        return mobile_phone
