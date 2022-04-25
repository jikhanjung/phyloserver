from django.contrib import admin
from .models import PhyloPackage, PhyloRun, PhyloModel, PhyloLeg, PhyloUser
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(PhyloPackage)
admin.site.register(PhyloRun)
admin.site.register(PhyloModel)
admin.site.register(PhyloLeg)

from .forms import PhyloUserCreationForm, PhyloUserChangeForm

class PhyloUserAdmin(UserAdmin):
    add_form = PhyloUserCreationForm
    form = PhyloUserChangeForm
    model = PhyloUser
    list_display = ["email", "username",]

admin.site.register(PhyloUser, PhyloUserAdmin)