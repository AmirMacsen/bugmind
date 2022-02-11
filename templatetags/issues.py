from django.template import Library
from django.shortcuts import reverse

register = Library()


@register.simple_tag
def string_just(num):
    if num < 100:
        num = str(num).rjust(3, "0")
    return f"#{num}"
