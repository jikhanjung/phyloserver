from django import forms
from django.db import models
from .models import RoseOccurrence
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class RoseOccurrenceForm(ModelForm):
    class Meta:
        model = RoseOccurrence
        fields = ['locality', 'age','comment','strike','dip']
