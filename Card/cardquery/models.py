from django.db import models

# Create your models here.
#定义用户表，存储学生的卡号和密码
class User(models.Model):
    uid=   models.AutoField(primary_key=True)
    idserial=models.CharField(max_length=20)
    cardpwd=models.CharField(max_length=25)
    def __str__(self):
        return self.idserial
