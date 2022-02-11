import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.urls import reverse

from accounts.decorators import login_required
from management.forms.issues import IssuesModelForm, IssuesReplyModelForm, InviteModelForm
from management.models import Issues, IssuesReply, IssuesType, ProjectInvite
from pricepolicy.models import Transaction, PricePolicy
from projects.models import ProjectUser
from utils.pagination.pagination import Pagination
from utils.encrypt.md5 import uid


class CheckFilter:
    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            ck = ""
            # 如果当前用户请求的url中status和当前循环的key相等
            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                ck = "checked"
                value_list.remove(key)
            else:
                value_list.append(key)
            # url
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            # 移除分页
            if 'page' in query_dict:
                query_dict.pop('page')

            query_param = query_dict.urlencode()
            if query_param:
                url = f"{self.request.path_info}?{query_dict.urlencode()}"
            else:
                url = self.request.path_info

            html = f"<a class='cell' href='{url}'><input type='checkbox' {ck} /><label>{text}</label></a>"
            yield mark_safe(html)


class SelectFilter:
    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        yield mark_safe("<select class='select2' multiple='multiple' style='width:100%;'>")
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            value_list = self.request.GET.getlist(self.name)
            selected = ""
            if key in value_list:
                selected = "selected"
                value_list.remove(key)
            else:
                value_list.append(key)

            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            param_url = query_dict.urlencode()

            if param_url:
                url = f"{self.request.path_info}?{param_url}"
            else:
                url = self.request.path_info

            html = f"<option value={url} {selected}>{text}</option>"
            yield mark_safe(html)

        yield mark_safe("</select>")


@login_required
def issues(request, project_id):
    if request.method == "GET":
        # 筛选条件（根据用户通过GET传过来的参数实现）
        # example: ?status=1&status=2$issues_type=1
        allow_filter_name = ['issues_type', 'status', 'priority']
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition[f"{name}__in"] = value_list
        # 分页获取数据
        queryset = Issues.objects.filter(project_id=project_id).filter(**condition)
        page_object = Pagination(
            current_page=request.GET.get("page"),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
        )
        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request)

        project_issues_type = IssuesType.objects.filter(project_id=project_id).values_list("id", "title")

        project_total_user = [(request.tracer.project.creator_id, request.tracer.project.creator.username)]
        project_join_user = ProjectUser.objects.filter(project_id=project_id).values_list("user_id", "user__username")
        project_total_user.extend(project_join_user)

        invite_form = InviteModelForm()
        context = {
            "form": form,
            "invite_form": invite_form,
            "issues_object_list": issues_object_list,
            "page_html": page_object.page_html(),
            'filter_list': [
                {'title': "问题类型", 'filter': CheckFilter('issues_type', project_issues_type, request)},
                {'title': "状态", 'filter': CheckFilter('status', Issues.status_choices, request)},
                {'title': "优先级", 'filter': CheckFilter('priority', Issues.priority_choices, request)},
                {'title': "指派者", 'filter': SelectFilter('assign', project_total_user, request)},
                {'title': "关注者", 'filter': SelectFilter('attention', project_total_user, request)},
            ]
        }
        return render(request, "management/issues.html", context)

    form = IssuesModelForm(request, data=request.POST)

    if form.is_valid():
        # 添加问题
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.save()
        return JsonResponse({"status": True})
        pass
    return JsonResponse({"status": False, "error": form.errors})


@login_required
def issues_detail(request, project_id, issues_id):
    issues_object = Issues.objects.filter(id=issues_id, project_id=project_id).first()
    form = IssuesModelForm(request, instance=issues_object)
    return render(request, "management/issues_detail.html", {"form": form, "issues_object": issues_object})


@login_required
def issues_record(request, project_id, issues_id):
    """初始化操作记录"""
    if request.method == "GET":
        reply_list = IssuesReply.objects.filter(issues_id=issues_id, issues__project=request.tracer.project)
        # 将queryset转换成json
        data_list = []
        for row in reply_list:
            data = {
                "id": row.id,
                "reply_type_text": row.get_reply_type_display(),
                "content": row.content,
                "creator": row.creator.username,
                "datetime": row.create_datetime.strftime("%Y-%m-%d %H:%M"),
                "parent_id": row.reply_id
            }
            data_list.append(data)
        return JsonResponse({"status": True, "data": data_list})
    form = IssuesReplyModelForm(data=request.POST)
    if form.is_valid():
        form.instance.issues_id = issues_id
        form.instance.reply_type = 2
        form.instance.creator = request.tracer.user
        instance = form.save()
        info = {
            "id": instance.id,
            "reply_type_text": instance.get_reply_type_display(),
            "content": instance.content,
            "creator": instance.creator.username,
            "datetime": instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            "parent_id": instance.reply_id
        }
        return JsonResponse({"status": True, "data": info})
    return JsonResponse({"status": False, "error": form.errors})


@login_required
def issues_change(request, project_id, issues_id):
    issues_object = Issues.objects.filter(id=issues_id, project_id=project_id).first()
    post_dict = json.loads(request.body)
    name = post_dict.get('name')
    value = post_dict.get('value')
    field_object = Issues._meta.get_field(name)

    def create_issues_record(change_record):
        """内部方法，用于生成操作记录"""
        new_obj = IssuesReply.objects.create(
            reply_type=1,
            issues=issues_object,
            content=change_record,
            creator=request.tracer.user
        )

        info = {
            "id": new_obj.id,
            "reply_type_text": new_obj.get_reply_type_display(),
            "content": new_obj.content,
            "creator": new_obj.creator.username,
            "datetime": new_obj.create_datetime.strftime("%Y-%m-%d %H:%M"),
            "parent_id": new_obj.reply_id
        }

        return info

    # 1.数据库字段更新
    # 1.1 文本
    if name in ['subject', 'desc', 'start_date', 'end_date']:
        if not value:
            if field_object.null:
                setattr(issues_object, name, None)
                issues_object.save()
                change_record = f"{field_object.verbose_name}更新为空"
            else:
                return JsonResponse({"status": False, "error": f"{field_object.verbose_name} 不能为空"})
        else:
            setattr(issues_object, name, value)
            issues_object.save()
            change_record = f"{field_object.verbose_name}更新为{value}"

        return JsonResponse({"status": True, "data": create_issues_record(change_record)})

    # 1.2 FK字段（关于指派，需要特殊的处理方式，因为前端有可能传递过来任意的用户，而在用户表中可以查询到）
    if name in ['issues_type', 'module', 'parent', 'assign']:
        # 用户选择为空
        if not value:
            if not field_object.null:
                return JsonResponse({"status": False, "error": f"{field_object.verbose_name} 不能为空"})
            # 允许为空
            setattr(field_object, name, None)
            issues_object.save()
            change_record = f"{field_object.verbose_name}更新为空"
        else:
            # 判断用户输入的值，是否可以查询到，这里比较重要，通过外键字段查询是否在对应的表中有记录
            if name == "assign":
                # 是否是项目的创建者
                if value == str(request.tracer.project.creator_id):
                    instance = request.tracer.project.creator
                else:
                    # 是否是项目的参与者
                    project_user_object = ProjectUser.objects.filter(project_id=project_id, user_id=value).first()
                    if project_user_object:
                        instance = project_user_object.user
                    else:
                        instance = None
                if not instance:
                    return JsonResponse({"status": False, "error": f"您选择的 {field_object.verbose_name} 不存在"})
                setattr(issues_object, name, instance)
                issues_object.save()
                change_record = f"{field_object.verbose_name}更新为{str(instance)}"
            else:
                # remote_field
                instance = field_object.remote_field.model.objects.filter(id=value, project_id=project_id).first()
                if not instance:
                    return JsonResponse({"status": False, "error": f"您选择的 {field_object.verbose_name} 不存在"})
                setattr(issues_object, name, instance)
                issues_object.save()
                change_record = f"{field_object.verbose_name}更新为{str(instance)}"

            return JsonResponse({"status": True, "data": create_issues_record(change_record)})

    # 1.3 choices字段
    if name in ['priority', 'status', 'mode']:
        selected_text = None
        for key, text in field_object.choices:
            if str(key) == value:
                selected_text = text
        if not selected_text:
            return JsonResponse({"status": False, 'error': f"您选择的 {field_object.verbose_name} 不存在"})
        setattr(issues_object, name, value)
        issues_object.save()
        change_record = f"{field_object.verbose_name}更新为{str(selected_text)}"
        return JsonResponse({"status": True, "data": create_issues_record(change_record)})
    # 1.4 M2M字段
    if name == "attention":
        # {"name":"attention","value":[1,2,3]}
        if not isinstance(value, list):
            return JsonResponse({"status": False, "error": "数据格式错误"})
        if not value:
            # 这个地方也很重要
            issues_object.attention.set([])
            issues_object.save()
            change_record = f"{field_object.verbose_name}更新为空"
        else:
            # 判断id是否是项目成员
            user_dict = {str(request.tracer.project.creator_id): request.tracer.project.creator.username}
            project_user_dict = ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_dict:
                user_dict[str(item.user_id)] = item.user.username
            username_list = []
            for user_id in value:
                if not user_dict.get(user_id):
                    return JsonResponse({"status": False, "error": "数据错误"})
                username_list.append(user_dict.get(user_id))

            issues_object.attention.set(value)
            issues_object.save()
            change_record = f"{field_object.verbose_name}更新为{','.join(username_list)}"

        return JsonResponse({"status": True, "data": create_issues_record(change_record)})

    return JsonResponse({"status": False, "error": "数据错误"})


@login_required
def invite_url(request, project_id):
    """生成邀请码"""
    form = InviteModelForm(data=request.POST)
    if form.is_valid():
        """
        1.创建一个随机的验证码
        2.将验证码保存到数据库
        3.限制：只有项目的创建者才可以邀请
        """
        if request.tracer.user != request.tracer.project.creator:
            form.add_error('period', "无权创建邀请码")
            return JsonResponse({"status": False, "error": form.errors})
        random_invite_code = uid(request.tracer.user.mobile_phone)
        form.instance.project = request.tracer.project
        form.instance.code = random_invite_code
        form.instance.creator = request.tracer.user
        form.save()

        # 将验证码返回到前端，用于前端展示
        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,
            host=request.get_host(),
            path=reverse('projects:invite_join', kwargs={'code': random_invite_code})
        )
        return JsonResponse({"status": True, "data": url})

    return JsonResponse({"status": False, "error": form.errors})


@login_required
def invite_join(request, code):
    """进入邀请"""
    current_datetime = datetime.datetime.now()
    invite_object = ProjectInvite.objects.filter(code=code).first()

    if not invite_object:
        return render(request, "management/invite_join.html", {"error": "邀请码不存在"})

    # 如果是项目成员则提示用户不用再加入项目
    if invite_object.project.creator == request.tracer.user:
        return render(request, "management/invite_join.html", {"error": "创建者无需再加入项目"})

    # 如果已经是项目成员了则不用再加入项目
    exists = ProjectUser.objects.filter(project=invite_object.project, user=request.tracer.user).exists()
    if exists:
        return render(request, "management/invite_join.html", {"error": "已加入项目，无需再加入项目"})

    # 容量的判断
    # 项目允许加入的最大的成员数量
    # max_member = request.tracer.price_policy.price_policy.project_member
    transaction_obj = Transaction.objects.filter(user=invite_object.project.creator).order_by('-id').first()
    if transaction_obj.price_policy.category == 1:
        max_member = transaction_obj.price_policy.project_member
    else:
        if transaction_obj.end_datetime.replace(tzinfo=None) < current_datetime:
            free_obj = PricePolicy.objects.filter(category=1).first()
            max_member = free_obj.project_member
        else:
            max_member = transaction_obj.price_policy.project_member

    # 目前项目的成员
    current_number = ProjectUser.objects.filter(project=invite_object.project).count()
    current_number += 1
    if current_number >= max_member:
        return render(request, "management/invite_join.html", {"error": "项目成员超过套餐上限"})

    # 邀请码本身的判断
    limit_datetime = invite_object.create_datetime + datetime.timedelta(minutes=invite_object.period)
    limit_datetime = limit_datetime.replace(tzinfo=None)
    if current_datetime > limit_datetime:
        return render(request, "management/invite_join.html", {"error": "邀请链接已过期"})

    # 数量校验
    if invite_object.count:
        if invite_object.use_count >= invite_object.count:
            return render(request, "management/invite_join.html", {"error": "超过邀请数量"})
        invite_object.use_count += 1
        invite_object.save()

    ProjectUser.objects.create(user=request.tracer.user, project=invite_object.project)
    invite_object.project.join_count += 1
    invite_object.project.save()
    return render(request, "management/invite_join.html", {'project': invite_object.project})