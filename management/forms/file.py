from django import forms
from django.core.exceptions import ValidationError

from accounts.forms import BootStrapForm
from management.models import File

from utils.tencent.cos import check_file


class NewFolderModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = File
        fields = ['name']

    def __init__(self, request, parent_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_obj = parent_obj

    def clean_name(self):
        name = self.cleaned_data['name']
        # 数据库判断当前目录下问价夹是否已经存在
        qs = File.objects.filter(file_type=1, name=name, project=self.request.tracer.project)
        if self.parent_obj:
            exists = qs.filter(parent=self.parent_obj).exists()
        else:
            exists = qs.filter(parent__isnull=True).exists()

        if exists:
            raise ValidationError("文件夹名称重复")

        return name


class FileModelForm(forms.ModelForm):
    etag = forms.CharField(label='Etag')

    class Meta:
        model = File
        exclude = ['project', 'file_type', 'updator', 'update_datetime']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_path(self):
        return "https://{}".format(self.cleaned_data['path'])

    def clean(self):
        etag = self.cleaned_data['etag']
        key = self.cleaned_data['key']
        size = self.cleaned_data['size']
        if not etag or not key:
            return self.cleaned_data
        # cos检验文件是否合法
        # 通过SDK校验
        from qcloud_cos.cos_exception import CosServiceError
        try:
            result = check_file(key=key,
                                bucket=self.request.tracer.project.bucket,
                                region=self.request.tracer.project.region)
        except CosServiceError as e:
            self.add_error(key, "文件不存在")
            return self.cleaned_data

        if etag != result.get('ETag'):
            self.add_error('etag', "Etag错误")

        if int(result.get('Content-Length')) != size:
            self.add_error("size", "文件大小错误")

        return self.cleaned_data
