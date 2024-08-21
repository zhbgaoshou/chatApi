from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Room(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='创建该会话的用户id')
    name = models.CharField(max_length=100, help_text='会话名字')

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, help_text='会话id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='用户id')
    content = models.TextField(help_text='消息内容')
    role = models.CharField(max_length=100, help_text='角色')
    model = models.CharField(max_length=100, help_text='模型')
    date_time = models.CharField(max_length=100, help_text='时间')

    def __str__(self):
        return self.content
