from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.safestring import mark_safe

class FrOccurrence(models.Model):
    locality = models.CharField(max_length=200,blank=True,null=True)
    country = models.CharField(max_length=200,blank=True,null=True)
    clade = models.CharField(max_length=200,blank=True,null=True)
    family = models.CharField(max_length=200,blank=True,null=True)
    genus = models.CharField(max_length=200,blank=True,null=True)
    origin = models.CharField(max_length=200,blank=True,null=True)
    epoch = models.CharField(max_length=200,blank=True,null=True)
    age = models.CharField(max_length=200,blank=True,null=True)
    environment = models.CharField(max_length=200,blank=True,null=True)
    continent = models.CharField(max_length=200,blank=True,null=True)
    period = models.CharField(max_length=200,blank=True,null=True)
    reference = models.CharField(max_length=200,blank=True,null=True)

    def __str__(self):
        return self.genus
    