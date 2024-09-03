from django.contrib.auth.models import User
from chat.models import Room
from django.db import models
import os
import uuid
from django.utils.text import slugify
from datetime import datetime


# 自定义文件名字
def user_directory_path(instance, filename):
    # 提取文件的扩展名
    ext = filename.split('.')[-1]

    # 使用 slugify 将文件名转为适合URL的格式
    filename = slugify(filename.rsplit('.', 1)[0])

    # 如果slugify处理后文件名为空，使用uuid生成一个新的文件名
    if not filename:
        filename = uuid.uuid4()

    # 最终文件名包括扩展名
    filename = f'{filename}.{ext}'

    # 生成文件上传路径: user/images/YYYY-MM-DD/
    return os.path.join('user/images', datetime.now().strftime('%Y-%m-%d'), filename)

class AiModel(models.Model):
    name = models.CharField(max_length=100, help_text='模型名字')
    description = models.TextField(help_text='模型描述')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False, help_text='是否默认模型')

    def __str__(self):
        return self.name

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_room = models.OneToOneField(Room, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(default='default.jpg', upload_to=user_directory_path, blank=True, null=True)
