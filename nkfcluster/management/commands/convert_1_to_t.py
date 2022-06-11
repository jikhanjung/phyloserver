from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, PbdbOccurrence, TotalOccurrence, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, NkfLocality
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

        TotalOccurrence.objects.filter(country='KR').delete()
        nkocc_list = NkfOccurrence.objects.filter(group='TR')
        #print(len(occ3_list))
        for nkocc in nkocc_list:

            #print(occ3.listed_name)
            occ = TotalOccurrence()
            #occ.index = occ4.index
            #occ.strat_unit = occ4.stratigraphy_code
            occ.country = 'KR'
            occ.group = nkocc.group
            occ.species_name = nkocc.species_name
            occ.genus_name = nkocc.genus_name
            location_code = nkocc.location
            for ( code, name ) in LOCATION_CHOICES:
                if location_code == code:
                    occ.locality_lvl3 = name
                    loc3 = NkfLocality.objects.get(name=name)
                    loc2 = loc3.parent
                    occ.locality_lvl2 = loc2.name
                    loc1 = loc2.parent
                    occ.locality_lvl1 = loc1.name
            occ.source = nkocc.source
            if nkocc.chronounit:
                occ.chrono_lvl2 = nkocc.chronounit.name
                occ.chrono_lvl1 = nkocc.chronounit.parent.name
                occ.save()

