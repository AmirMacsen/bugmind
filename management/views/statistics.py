import collections

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from accounts.decorators import login_required
from management import models
from projects.models import ProjectUser


@login_required
def statistics(request, project_id):
    return render(request, "management/statistics.html")


@login_required
def statistics_priority(request, project_id):
    """ 按照优先级生成饼图 """
    """
    data_list = [
      {
         "name": "Internet Explorer",
         "y": 11
      },
      {
         "name": "Internet Explorer",
         "y": 11
      }
    ]
    """
    # 1. 构造字典
    data_dict = {}
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}
    # 2.去数据库查询所有分组得到的数据
    start = request.GET.get("start")
    end = request.GET.get("end")

    result = models.Issues.objects.filter(project_id=project_id,
                                          create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))

    # 3.分组得到的数据更新到data_dict
    for item in result:
        data_dict[item['priority']]['y'] = item['ct']
    return JsonResponse({"status": True, "data": list(data_dict.values())})


@login_required
def project_user(request, project_id):
    """ 项目中每个成员被分配的问题及其数量 """
    """
    context = {
        "status":True,
        "data": {
            'categories': ['juaner', 'amir'],
            'series': [
                {
                    "name": "新建",
                    "data": [1,2],
                },
                {
                    "name": "新建",
                    "data": [1,2],
                },
            ]
        }
    }
    """

    # 1.先构造一个字典
    """
    info = {
        1: {
            name: "amir",
            status: {
                1:0,
                2:0,
                3:0,
                4:0,
                5:0,
                6:0,
                7:0,
            }
        },
        2: {
            name: "juaner",
            status: {
                1:0,
                2:0,
                3:0,
                4:0,
                5:0,
                6:0,
                7:0,
            }
        }
    }
    """
    all_user_dict = {
        request.tracer.project.creator.id: {
            'name': request.tracer.project.creator.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        },
        None: {
            'name': "未指派",
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }
    }

    user_list = ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            "name": item.user.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }

    # 2.从数据库中查出所有问题，然后填充字典的series
    start = request.GET.get("start")
    end = request.GET.get("end")

    issues = models.Issues.objects.filter(project_id=project_id,
                                          create_datetime__gte=start,
                                          create_datetime__lt=end)

    for item in issues:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1

    # 3.从字典中遍历出所有的name，生成categories
    categories = [data['name'] for data in all_user_dict.values()]

    # 4.构造最终的数据
    """
    info = {
        1: {"name":"新建", data: []},
        2: {"name":"处理中", data: []},
        3: {"name":"已解决", data: []},
        4: {"name":"已忽略", data: []},
        5: {"name":"待反馈", data: []},
        6: {"name":"已关闭", data: []},
        7: {"name":"重新打开", data: []},
    }
    """
    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {"name": item[1], "data": []}

    for key, text in models.Issues.status_choices:
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    context = {
        'status': True,
        'data': {
            "categories": categories,
            'series': list(data_result_dict.values())
        }
    }

    return JsonResponse(context)

