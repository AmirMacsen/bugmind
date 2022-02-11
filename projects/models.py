from django.db import models

from accounts.models import UserInfo


class Project(models.Model):
    """项目表"""
    COLOR_CHOICES = (
        (1, "#56b8eb"),  # 56b8eb
        (2, "#f28033"),  # f28033
        (3, "#ebc656"),  # ebc656
        (4, "#a2d148"),  # a2d148
        (5, "#20BFA4"),  # #20BFA4
        (6, "#7461c2"),  # 7461c2,
        (7, "#20bfa3"),  # 20bfa3,
    )
    name = models.CharField(verbose_name='项目名', max_length=32)
    color = models.SmallIntegerField(verbose_name='颜色', choices=COLOR_CHOICES, default=1)
    desc = models.CharField(verbose_name='项目描述', max_length=255, null=True, blank=True)

    use_space = models.BigIntegerField(verbose_name='项目已使用空间', default=0, help_text='字节')

    star = models.BooleanField(verbose_name='星标', default=False)

    join_count = models.SmallIntegerField(verbose_name='参与人数', default=1)
    creator = models.ForeignKey(UserInfo, verbose_name='创建者', related_name="project_creator", on_delete=models.CASCADE)
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    bucket = models.CharField(verbose_name='cos桶', max_length=128)
    region = models.CharField(verbose_name='cos区域', max_length=32)

    # 对many to many 的说明
    # 这里指定了多对多的一个关系，如果没有指定through，则会生成一张表，表示了project和user的一个对应关系，
    # 但是如果指定through，则会使用指定的表实现这个关系。而且要定义好through_fields，其中字段的顺序要与ProjectUser定义的顺序一致
    # 这种字段定义在查询的时候有效，但是在增加、删除、修改的时候没有作用
    # project_user = models.ManyToManyField(to="UserInfo", through="ProjectUser", through_fields=("project", "user"))

    class Meta:
        verbose_name_plural = "项目列表"

    def __str__(self):
        return self.name


class ProjectUser(models.Model):
    """ 项目参与者 """
    project = models.ForeignKey(Project, verbose_name='项目', related_name="project_user", on_delete=models.CASCADE)
    user = models.ForeignKey(UserInfo, verbose_name='参与者', related_name="project_userInfo", on_delete=models.CASCADE)
    star = models.BooleanField(verbose_name='星标', default=False)
    created = models.DateTimeField(verbose_name='加入时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "项目成员"

    def __str__(self):
        return f"ProjectUser: {self.project}  {self.user}"
