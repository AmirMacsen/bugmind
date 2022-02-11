from django.db import models

from accounts.models import UserInfo
from projects.models import Project


class Wiki(models.Model):
    project = models.ForeignKey(Project, verbose_name="项目", related_name="wiki", on_delete=models.CASCADE)
    title = models.CharField(verbose_name="标题", max_length=32)
    content = models.TextField(verbose_name="内容")

    # 自关联
    parent = models.ForeignKey(to="Wiki",
                               verbose_name="父文章",
                               related_name="children",
                               null=True,
                               blank=True,
                               on_delete=models.SET_NULL)

    depth = models.SmallIntegerField(verbose_name="深度", default=1)

    def __str__(self):
        return self.title


class File(models.Model):
    FILE_TYPE = (
        (1, "文件夹"),
        (2, "文件")
    )
    project = models.ForeignKey(Project, related_name="files", on_delete=models.CASCADE, verbose_name="项目")
    name = models.CharField(verbose_name="名称", max_length=128)
    file_type = models.IntegerField(choices=FILE_TYPE, verbose_name="类型")
    key = models.CharField(verbose_name="key", max_length=128, null=True, blank=True)
    size = models.BigIntegerField(verbose_name="文件大小", null=True, help_text="字节")
    path = models.CharField(verbose_name="文件路径", max_length=255, null=True, blank=True)
    parent = models.ForeignKey(to="File", related_name="children",
                               on_delete=models.CASCADE, null=True, blank=True, verbose_name="父目录")
    updator = models.ForeignKey(UserInfo, related_name="user_files",
                                null=True, blank=True, on_delete=models.SET_NULL,
                                verbose_name="更换者")
    update_datetime = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name_plural = "文件列表"

    def __str__(self):
        return self.name


# 问题相关

class Module(models.Model):
    """模块（里程碑）"""
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name="modules",
                                verbose_name="项目")
    title = models.CharField(verbose_name="模块名称", max_length=32)

    def __str__(self):
        return self.title


class IssuesType(models.Model):
    """问题类型 (任务、功能、bug...)"""
    PROJECT_INIT_LIST = ["任务", '功能', 'Bug']
    title = models.CharField(max_length=32, verbose_name="类型名称")
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name="issues_type",
                                verbose_name="项目")

    def __str__(self):
        return self.title


class Issues(models.Model):
    """ 问题 """
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name="issues",
                                verbose_name='项目')
    issues_type = models.ForeignKey(IssuesType,
                                    on_delete=models.CASCADE,
                                    related_name="type_issues",
                                    verbose_name='问题类型')
    module = models.ForeignKey(Module,
                               on_delete=models.CASCADE,
                               related_name="module_issues",
                               verbose_name='模块',
                               null=True, blank=True)

    subject = models.CharField(verbose_name='主题', max_length=80)
    desc = models.TextField(verbose_name='问题描述')

    priority_choices = (
        ("danger", "高"),
        ("warning", "中"),
        ("success", "低"),
    )
    priority = models.CharField(verbose_name='优先级',
                                max_length=12,
                                choices=priority_choices,
                                default='danger')

    # 新建、处理中、已解决、已忽略、待反馈、已关闭、重新打开
    status_choices = (
        (1, '新建'),
        (2, '处理中'),
        (3, '已解决'),
        (4, '已忽略'),
        (5, '待反馈'),
        (6, '已关闭'),
        (7, '重新打开'),
    )
    status = models.SmallIntegerField(verbose_name='状态',
                                      choices=status_choices,
                                      default=1)

    assign = models.ForeignKey(UserInfo,
                               verbose_name='指派',
                               related_name='task',
                               on_delete=models.CASCADE,
                               null=True, blank=True)
    attention = models.ManyToManyField(UserInfo,
                                       verbose_name='关注者',
                                       related_name='observe',
                                       blank=True, )

    start_date = models.DateField(verbose_name='开始时间', null=True, blank=True)
    end_date = models.DateField(verbose_name='结束时间', null=True, blank=True)

    mode_choices = (
        (1, '公开模式'),
        (2, '隐私模式'),
    )
    mode = models.SmallIntegerField(verbose_name='模式', choices=mode_choices, default=1)

    parent = models.ForeignKey(verbose_name='父问题',
                               to='self', related_name='child',
                               null=True, blank=True,
                               on_delete=models.SET_NULL)

    creator = models.ForeignKey(UserInfo, verbose_name='创建者',
                                on_delete=models.CASCADE,
                                related_name='create_problems')

    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    latest_update_datetime = models.DateTimeField(verbose_name='最后更新时间', auto_now=True)

    def __str__(self):
        return self.subject


class IssuesReply(models.Model):
    """ 问题回复"""

    reply_type_choices = (
        (1, '修改记录'),
        (2, '回复')
    )
    reply_type = models.IntegerField(verbose_name='类型', choices=reply_type_choices)

    issues = models.ForeignKey(Issues, on_delete=models.CASCADE, related_name="replies", verbose_name='问题')
    content = models.TextField(verbose_name='描述')
    creator = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name="create_reply", verbose_name='创建者')
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    reply = models.ForeignKey(verbose_name='回复', to='self', on_delete=models.CASCADE, null=True, blank=True)


class ProjectInvite(models.Model):
    """ 项目邀请码 """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='项目')
    code = models.CharField(verbose_name='邀请码', max_length=64, unique=True)
    count = models.PositiveIntegerField(verbose_name='限制数量', null=True, blank=True, help_text='空表示无数量限制')
    use_count = models.PositiveIntegerField(verbose_name='已邀请数量', default=0)
    period_choices = (
        (30, '30分钟'),
        (60, '1小时'),
        (300, '5小时'),
        (1440, '24小时'),
    )
    period = models.IntegerField(verbose_name='有效期', choices=period_choices, default=1440)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    creator = models.ForeignKey(UserInfo, on_delete=models.CASCADE, verbose_name='创建者', related_name='create_invite')
