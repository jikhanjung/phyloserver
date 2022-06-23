from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, NkfOccurrence5, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, ChronoUnit
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

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)
        NkfOccurrence.objects.filter(source_code='5').delete()

        occ5_list = NkfOccurrence5.objects.all()
        
        for occ5 in occ5_list:
            if occ5.geologic_period == "Neoproterozoic":
                continue
            #print(occ3.listed_name)
            occ = NkfOccurrence()
            occ.index = occ5.index
            occ.strat_unit = occ5.stratigraphy_code
            occ.location = occ5.locality_code
            occ.lithology = occ5.lithology
            occ.group = occ5.fossil_group_code
            occ.species_name = occ5.listed_species
            occ.process_genus_name()
            occ.source = occ5.author_list + "(" + occ5.year + ":" + occ5.issue + ")"
            occ.source_code = '5'
            chrono_list = []
            chrono_list.append(occ5.from_chronounit)
            if occ5.from_chronounit != occ5.to_chronounit:
                chrono_list.append(occ5.to_chronounit)
            for chrono_name in chrono_list:
                chrono_unit = ChronoUnit.objects.get(name=chrono_name)
                if chrono_unit:
                    occ.chronounit = chrono_unit
                    #print(occ.chronounit)
                    occ.save()

            #occ.save()

