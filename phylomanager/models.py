from django.db import models

# Create your models here.

class PhyloPackage(models.Model):
    package_name = models.CharField(max_length=200)
    package_type = models.CharField(max_length=200)
    run_path = models.CharField(max_length=200)

class PhyloRun(models.Model):
    start_datetime = models.DateTimeField()
    finish_datetime = models.DateTimeField()
    run_title = models.CharField(max_length=200)
    run_status = models.CharField(max_length=10)
    run_by = models.CharField(max_length=200)
