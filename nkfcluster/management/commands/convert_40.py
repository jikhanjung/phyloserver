from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, ChronoUnit
from django.core.management.base import BaseCommand
import subprocess
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal
import matplotlib.pyplot as plt
from Bio import Phylo
import io
import pandas as pd
from django.db.models import Q

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)
        NkfOccurrence.objects.filter(Q(source_code='4')&~Q(chronounit__name='Neoproterozoic')).delete()

        occ_list = NkfOccurrence4.objects.all()
        #print(len(occ3_list))
        for occ4 in occ_list:
            if occ4.geologic_period == "Neoproterozoic":
                continue
            #print(occ3.listed_name)
            occ = NkfOccurrence()
            occ.index = occ4.index
            occ.strat_unit = occ4.stratigraphy_code
            occ.location = occ4.locality_code
            occ.group = occ4.fossil_group_code
            occ.species_name = occ4.listed_species
            occ.process_genus_name()
            occ.source = occ4.author_list + "(" + occ4.year + ":" + occ4.issue + ")"
            occ.source_code = '4'
            chrono_unit = ChronoUnit.objects.get(name=occ4.geologic_period)
            if chrono_unit:
                occ.chronounit = chrono_unit
            occ.save()

