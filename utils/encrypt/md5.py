import hashlib
import uuid

from django.conf import settings


def md5(string: str) -> str:
    """
    密码加密
    :param string: 明文
    :return: 密文
    """
    hash_obj = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_obj.update(string.encode("utf-8"))
    return hash_obj.hexdigest()


def uid(string):
    """生成随机图片名称用于上传到cos时保证文件名的唯一性"""
    data = "{}-{}".format(str(uuid.uuid4()), string)
    return md5(data)
