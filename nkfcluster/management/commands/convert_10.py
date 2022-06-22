from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence1, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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

        NkfOccurrence.objects.filter(source_code='1').delete()

        group_by_result = NkfOccurrence1.objects.raw("SELECT 1 as id, species_name, strat_unit, location, group, source, '1' as source_code FROM nkfcluster_nkfoccurrence1")
        for occ1 in group_by_result:
            occ0 = NkfOccurrence()
            occ0.species_name = occ1.species_name
            occ0.strat_unit = occ1.strat_unit
            occ0.location = occ1.location
            occ0.group = occ1.group
            occ0.source = occ1.source
            occ0.source_code = occ1.source_code
            occ0.process_genus_name()
            occ0.save()
            #print(occ1.species_name, occ1.location, occ1.strat_unit)