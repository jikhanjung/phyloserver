from django.db import models

# Create your models here.
class DolfinImage(models.Model):
    ipaddress = models.CharField(max_length=100, blank=True, default='')
    filepath = models.CharField(max_length=200, blank=True, default='')
    filename = models.CharField(max_length=100, blank=True, default='')
    md5hash = models.CharField(max_length=200, blank=True, default='')
    imagefile = models.ImageField(upload_to ='%Y/%m/%d/')
