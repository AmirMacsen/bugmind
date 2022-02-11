from django.db import models


class UserInfo(models.Model):
    username = models.CharField(verbose_name="用户名", max_length=20, db_index=True)
    email = models.EmailField(verbose_name="邮箱", max_length=32)
    mobile_phone = models.CharField(verbose_name="手机号", unique=True, max_length=32)
    password = models.CharField(verbose_name="密码", max_length=100)

    class Meta:
        verbose_name_plural = "用户信息"

    def __str__(self):
        return self.username
