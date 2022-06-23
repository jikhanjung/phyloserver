from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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

        occ3_list = NkfOccurrence3.objects.all()
        #print(len(occ3_list))
        for occ3 in occ3_list:
            #print(occ3.listed_name)
            if occ3.listed_name.find(";") > 0:
                continue
            genus_list = [ x.strip() for x in occ3.listed_name.split(",") ]
            strat_list = [ x.strip() for x in occ3.stratigraphy.split(",") ]
            locality_list = [ x.strip() for x in occ3.locality.split(",") ]
            for genus in genus_list:
                for strat in strat_list:
                    for loc in locality_list:
                        occ1 = NkfOccurrence()
                        occ1.index = occ3.index
                        occ1.strat_unit = self.find_strat(strat)
                        occ1.location = self.find_loc(loc)
                        occ1.group = self.find_group(genus)
                        occ1.species_name = genus
                        occ1.genus_name = genus
                        occ1.source = occ3.author + "(" + occ3.year + ":" + occ3.issue + ")"
                        occ1.source_code = '3'
                        occ1.save()

    def find_strat(self,strat):
        return strat[:10]

    def find_loc(self,loc):
        return loc[:10]

    def find_group(self,genus):
        return genus[:10]
