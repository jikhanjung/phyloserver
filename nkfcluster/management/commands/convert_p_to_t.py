from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, PbdbOccurrence, TotalOccurrence, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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
        count = 0

        TotalOccurrence.objects.filter(country='CN').delete()
        pocc_list = PbdbOccurrence.objects.all()
        #print(len(occ3_list))
        for pocc in pocc_list:

            #print(occ3.listed_name)
            for chrono in pocc.chrono_list.split(", "):
                occ = TotalOccurrence()
                #occ.index = occ4.index
                #occ.strat_unit = occ4.stratigraphy_code
                occ.country = 'CN'
                occ.group = 'TR'
                occ.species_name = pocc.species_name
                occ.genus_name = pocc.genus_name
                occ.locality_lvl1 = pocc.region
                occ.locality_lvl2 = pocc.region
                occ.locality_lvl3 = pocc.region
                occ.source = 'PBDB'
                occ.chrono_lvl1 = 'Cambrian'
                occ.chrono_lvl2 = chrono
                occ.save()
                count += 1

        message = "PBDB 자료 " + str(count) + " 건이 변환되었습니다."
        
        return message

