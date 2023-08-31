from django import forms
from django.db import models
from .models import FrOccurrence
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class FrOccurrenceForm(ModelForm):
    class Meta:
        model = FrOccurrence
        fields = ['locality', 'country', 'clade','family','genus','origin','epoch','age','environment','continent','period','reference']
