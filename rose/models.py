from django.db import models

# Create your models here.
class RoseOccurrence(models.Model):
    locality = models.CharField(max_length=200,blank=True,null=True)
    age = models.CharField(max_length=200,blank=True,null=True)
    comment = models.CharField(max_length=200,blank=True,null=True)
    strike = models.CharField(max_length=200,blank=True,null=True)
    dip = models.CharField(max_length=200,blank=True,null=True)
