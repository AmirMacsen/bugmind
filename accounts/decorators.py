from functools import wraps
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.http import QueryDict
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import resolve_url

REDIRECT_FIELD_NAME = 'next'


class AjaxHttpResponseRedirect(HttpResponseRedirectBase):
    status_code = 599
    # content_type = "application/json; charset=utf-8"


class HttpResponseRedirect(HttpResponseRedirectBase):
    status_code = 302


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """需要登录视图装饰器"""
    actual_decorator = user_passes_test(
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def user_passes_test(login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.tracer.user:
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            # login_url不传，默认是settings.LOGIN_URL,官方文档默认为/accounts/login/
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # 获取resolved_login_url的地址和协议
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            ajax = None
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                ajax = True
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name, ajax)

        return _wrapped_view

    return decorator


def redirect_to_login(next, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME, ajax=False):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    resolved_url = resolve_url(login_url or settings.LOGIN_URL)

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')
    if ajax:
        return AjaxHttpResponseRedirect(urlunparse(login_url_parts))

    return HttpResponseRedirect(urlunparse(login_url_parts))
