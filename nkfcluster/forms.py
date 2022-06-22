from django import forms
from django.db import models
from .models import NkfOccurrence, NkfOccurrence1, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, NkfOccurrence5, PbdbOccurrence, NkfLocality, ChronoUnit
from django.forms import ModelForm, inlineformset_factory, modelformset_factory

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.conf import settings

class NkfOccurrenceForm(ModelForm):
    class Meta:
        model = NkfOccurrence
        fields = ['strat_unit', 'chronounit', 'lithology','group','species_name','revised_species_name','location','source']

class NkfOccurrenceForm1(ModelForm):
    class Meta:
        model = NkfOccurrence1
        fields = ['strat_unit', 'chronounit', 'lithology','group','species_name','revised_species_name','location','source']

class NkfOccurrenceForm2(ModelForm):
    class Meta:
        model = NkfOccurrence2
        fields = ['type', 'plate','figure','species','preservation','preservation_eng','location','unit','unit_eng', 'strat_range', 'latitude','longitude','source']

class NkfOccurrenceForm3(ModelForm):
    class Meta:
        model = NkfOccurrence3
        fields = ['author','year','publication','issue','pages','geologic_period','fossil_group','fossil_group_code','locality','locality_code',
        'stratigraphy','stratigraphy_code','lithology','figure','implication','title','listed_name', 'note']

class NkfOccurrenceForm4(ModelForm):
    class Meta:
        model = NkfOccurrence4
        fields = ['author1','author2','author3','author4','author_list','year','publication','issue','pages','geologic_period','fossil_group','fossil_group_code','locality','locality_code',
        'stratigraphy','stratigraphy_code','lithology','figure','implication','title','listed_species', 'note']

class NkfOccurrenceForm5(ModelForm):
    class Meta:
        model = NkfOccurrence5
        fields = ['author1','author2','author3','author4','author_list','year','publication','issue','pages','geologic_period','fossil_group','fossil_group_code','locality','locality_code',
        'stratigraphy','stratigraphy_code','lithology','figure','implication','title','listed_species', 'note']

class PbdbOccurrenceForm(ModelForm):
    class Meta:
        model = PbdbOccurrence
        fields = ['occno', 'collno', 'species_name','genus_name','revised_species_name','group',
                    'early_interval','late_interval','max_ma','min_ma','chrono_from','chrono_to','chrono_list',
                    'latitude','longitude','country','state','county','region','formation','remarks']

class NkfLocalityForm(ModelForm):
    class Meta:
        model = NkfLocality
        fields = ['index', 'name','level','parent']

class ChronoUnitForm(ModelForm):
    class Meta:
        model = ChronoUnit
        fields = ['name', 'level', 'begin', 'end', 'parent']
