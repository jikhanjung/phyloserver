from django import forms
from django.db import models
from .models import FrOccurrence
from django.forms import ModelForm, inlineformset_factory, modelformset_factory
from nkfcluster.models import ChronoUnit
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class FrOccurrenceForm(ModelForm):

    period_code = forms.ModelChoiceField(queryset=ChronoUnit.objects.filter(level='3'), required=False, label='Period Code')
    epoch_code = forms.ModelChoiceField(queryset=ChronoUnit.objects.filter(level='2'), required=False, label='Epoch Code')
    age_code = forms.ModelChoiceField(queryset=ChronoUnit.objects.filter(level='1'), required=False, label='Age Code')

    class Meta:
        model = FrOccurrence
        #fields = ['locality', 'country', 'clade','family','genus','origin','epoch','age','environment','continent','period','reference']
        fields = ['locality', 'country', 'clade', 'family', 'genus', 'origin', 'epoch', 'age', 'environment', 'continent', 'period', 'reference', 'period_code', 'epoch_code', 'age_code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['period_code'].queryset = ChronoUnit.objects.filter(level='3')
        self.fields['epoch_code'].queryset = ChronoUnit.objects.filter(level='2')
        self.fields['age_code'].queryset = ChronoUnit.objects.filter(level='1')