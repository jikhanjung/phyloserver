from django import forms
from django.db import models
from .models import PhyloLeg, PhyloModel, PhyloPackage, PhyloRun, PhyloUser
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class PhyloModelForm(ModelForm):
    class Meta:
        model = PhyloModel
        fields = ['model_name', 'model_type']

class PhyloRunForm(ModelForm):
    class Meta:
        model = PhyloRun
        fields = ['run_title', 'run_status', 'run_by', 'datafile', 'datatype', 'run_directory', 'start_datetime','finish_datetime']

class PhyloLegForm(ModelForm):
    class Meta:
        model = PhyloLeg
        fields = ['leg_title', 'leg_package','leg_type','leg_status','start_datetime','finish_datetime',
                  'ml_bootstrap','ml_bootstrap_type','substitution_model',
                  'mcmc_burnin','mcmc_relburnin','mcmc_burninfrac','mcmc_ngen','mcmc_printfreq','mcmc_samplefreq','mcmc_nruns','mcmc_nchains','mcmc_nst','mcmc_nrates']

class PhyloPackageForm(ModelForm):
    class Meta:
        model = PhyloPackage
        fields = ['package_name', 'package_version', 'package_type', 'run_path']

class PhyloUserRegisterForm(UserCreationForm):
    class Meta:
        model = PhyloUser
        fields = ("username", "lastname", "firstname", "email")

class PhyloUserChangeForm(UserChangeForm):

    class Meta:
        model = PhyloUser
        fields = ("username", "lastname", "firstname", "email")