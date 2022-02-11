from django import forms
from django.core.exceptions import ValidationError

from accounts.forms import BootStrapForm
from accounts.models import UserInfo
from pricepolicy.models import PricePolicy
from .models import Project
from .widgets import ColorRadioSelect


class ProjectModelForm(BootStrapForm, forms.ModelForm):
    bootstrap_exclude_field = ['color']

    class Meta:
        model = Project
        fields = ['name', 'color', 'desc']
        widgets = {
            "desc": forms.Textarea(attrs={"row": 5}),
            "color": ColorRadioSelect(attrs={"class": "color-radio"})
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        name = self.cleaned_data['name']
        # 当前用户是否已经创建过这个项目
        exist = Project.objects.filter(name=name, creator=self.request.tracer.user).exists()
        if exist:
            raise ValidationError(f"项目名称:{name}已经存在")
        # 当前用户是否还有额度创建项目
        user: UserInfo = self.request.tracer.user
        price_policy = self.request.tracer.price_policy.price_policy
        max_project_num = price_policy.project_num
        current_project_num = Project.objects.filter(creator=user).count()

        if current_project_num > max_project_num:
            raise ValidationError("您无法创建更多项目，请购买套餐获取更多的权限")
        return name
