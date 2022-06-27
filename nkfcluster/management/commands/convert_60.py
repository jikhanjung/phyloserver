from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence6, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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

        NkfOccurrence.objects.filter(source_code='6').delete()

        group_by_result = NkfOccurrence6.objects.raw('SELECT 1 as id, type_code, species, unit_code, location_code, source, COUNT(location_code) FROM nkfcluster_nkfoccurrence2 GROUP BY type_code, species, unit_code, location_code, source')
        for occ2 in group_by_result:
            occ1 = NkfOccurrence()
            occ1.species_name = occ2.species
            occ1.strat_unit = occ2.unit_code
            occ1.location = occ2.location_code
            occ1.group = occ2.type_code
            occ1.source = occ2.source
            occ1.source_code = '6'
            occ1.process_genus_name()
            occ1.save()
            #print(occ1.species_name, occ1.location, occ1.strat_unit)