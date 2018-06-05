from django.db import models

# Create your models here.
#定义用户表，存储学生的卡号和密码
class User(models.Model):
    uid=   models.AutoField(primary_key=True)
    idserial=models.CharField(max_length=20)
    cardpwd=models.CharField(max_length=25)
    def __str__(self):
        return self.idserial

class List(models.Model):
    lid = models.CharField(max_length=20,primary_key=True)
    shop = models.CharField(max_length=20,default='无')
    dir = models.CharField(max_length=10,default='无')
    def __str__(self):
        return self.lid
