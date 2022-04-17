from django import forms
from django.db import models
from .models import PhyloLeg, PhyloModel, PhyloPackage, PhyloRun
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User

from django.conf import settings

class PhyloModelForm(ModelForm):
    class Meta:
        model = PhyloModel
        fields = ['model_name', 'model_type']

class PhyloRunForm(ModelForm):
    class Meta:
        model = PhyloRun
        fields = ['run_title', 'run_status', 'run_by', 'run_directory']

class PhyloLegForm(ModelForm):
    class Meta:
        model = PhyloLeg
        fields = ['leg_title', 'leg_status', 'leg_package','start_datetime','finish_datetime','ml_bootstrap','ml_bootstrap_type','substitution_model',
                  'mcmc_burnin','mcmc_relburnin','mcmc_burninfrac','mcmc_ngen','mcmc_printfreq','mcmc_samplefreq','mcmc_nruns','mcmc_nchains']

class PhyloPackageForm(ModelForm):
    class Meta:
        model = PhyloPackage
        fields = ['package_name', 'package_version', 'package_type', 'run_path']