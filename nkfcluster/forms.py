from django import forms
from django.db import models
from .models import NkfOccurrence, NkfOccurrence2
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class NkfOccurrenceForm(ModelForm):
    class Meta:
        model = NkfOccurrence
        fields = ['strat_unit', 'lithology','group','species_name','location','source']

class NkfOccurrenceForm2(ModelForm):
    class Meta:
        model = NkfOccurrence2
        fields = ['type', 'plate','figure','species','preservation','preservation_eng','location','unit','unit_eng', 'strat_range', 'latitude','longitude','source']
