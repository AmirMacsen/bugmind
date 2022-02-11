from django.db import models

from accounts.models import UserInfo


class PricePolicy(models.Model):
    """套餐配置"""
    category_choice = (
        (1, '免费版'),
        (2, '收费版'),
        (3, '其他'),
    )

    category = models.SmallIntegerField(verbose_name="收费类型", choices=category_choice)
    title = models.CharField(verbose_name="标题", max_length=32)
    price = models.DecimalField(verbose_name="价格", max_digits=10, decimal_places=2)

    project_num = models.PositiveIntegerField(verbose_name="项目数")
    project_member = models.PositiveIntegerField(verbose_name="项目成员数")
    project_space = models.PositiveIntegerField(verbose_name="单项目空间（G）", help_text="G")
    per_file_size = models.PositiveIntegerField(verbose_name="单文件大小（M）", help_text="M")

    created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name_plural = "价格策略"

    def __str__(self):
        return self.title


class Transaction(models.Model):
    """交易记录"""
    status_choice = (
        (1, "未支付"),
        (2, "已支付")
    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choice)

    order = models.CharField(verbose_name="订单号", max_length=64, unique=True)
    user = models.ForeignKey(UserInfo, verbose_name="用户",
                             related_name="user_transactions", on_delete=models.PROTECT)
    price_policy = models.ForeignKey(PricePolicy, verbose_name="价格策略",
                                     related_name="policy_transactions", on_delete=models.PROTECT)
    count = models.IntegerField(verbose_name="数量(年)", help_text="0表示无限期")
    price = models.DecimalField(verbose_name="价格", max_digits=10, decimal_places=2)

    start_datetime = models.DateTimeField(verbose_name="开始时间", null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, default=None)

    created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name_plural = "交易记录"

    def __str__(self):
        return self.order
