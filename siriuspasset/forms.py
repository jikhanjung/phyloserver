from django import forms
from django.db import models
from .models import SpFossilSpecimen, SpFossilImage, SpSlab
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class SpFossilSpecimenForm(ModelForm):
    class Meta:
        model = SpFossilSpecimen
        fields = ['specimen_no', 'taxon_name', 'phylum', 'remarks', 'counterpart']


class SpFossilImageForm(ModelForm):
    class Meta:
        model = SpFossilImage
        fields = ['image_file','description']


class SpSlabForm(ModelForm):
    class Meta:
        model = SpSlab
        fields = ['slab_no', 'horizon', 'location', 'counterpart']