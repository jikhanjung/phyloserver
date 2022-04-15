from django.contrib import admin
from .models import PhyloPackage, PhyloRun, PhyloModel, PhyloLeg

# Register your models here.
admin.site.register(PhyloPackage)
admin.site.register(PhyloRun)
admin.site.register(PhyloModel)
admin.site.register(PhyloLeg)