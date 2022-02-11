import datetime
import time

from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse

from accounts.decorators import login_required
from management import models
from projects.models import ProjectUser


@login_required
def dashboard(request, project_id):
    # 问题数据处理
    status_dict = {}
    for key, text in models.Issues.status_choices:
        status_dict[key] = {"text": text, 'count': 0}
    issues_data = models.Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count("id"))
    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']
    # 项目成员
    user_list = ProjectUser.objects.filter(project_id=project_id).values('user_id', "user__username")

    # 获取前10个问题
    top_ten = models.Issues.objects.filter(project_id=project_id, assign__isnull=False).order_by('-id')[0:10]
    context = {
        "status_dict": status_dict,
        "user_list": user_list,
        "top_ten_object": top_ten
    }
    return render(request, "management/dashboard.html", context)


@login_required
def dashboard_chart(request, project_id):
    # 最近30天， 每天创建的问题的数量
    # 去数据库中查询最近30天所有的数据,根据年月日进行分组
    current_date = datetime.datetime.now().date()
    # 构造一个时间结构
    """
    {
        2022-02-12: [16788989898,0],
        2022-02-12: [16788989898,0],
        2022-02-12: [16788989898,0],
        2022-02-12: [16788989898,0],
    }
    """
    date_dict = {}
    for i in range(30):
        date = current_date - datetime.timedelta(days=i)
        date_dict[date.strftime("%Y-%m-%d")] = [time.mktime(date.timetuple()) * 1000, 0]
    # 下面select中是sqlite的时间格式化函数
    # 如果使用mysql， 则使用 “DATE_FORMAT(management_issues.create_datetime, '%%Y-%%m-%%d')”
    result = models.Issues.objects.filter(project_id=project_id,
                                          create_datetime__gte=current_date - datetime.timedelta(days=30)).extra(
        select={'ctime': "strftime('%%Y-%%m-%%d', management_issues.create_datetime) "}).values('ctime').annotate(ct=Count('id'))
    for item in result:
        date_dict[item['ctime']][1] = item['ct']
    return JsonResponse({'status': True, "data": list(date_dict.values())})
