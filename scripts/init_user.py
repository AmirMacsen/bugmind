import base
from accounts import models

print(models.UserInfo.objects.filter(username="admin").first())