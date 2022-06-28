from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence6, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, ChronoUnit
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

STRAT_RANGE_CHOICES = [
("S1", "Llandovery"),
("O3", "Upper Ordovician"),
("J1_basal (lime congl.)", "Jurassic"),
("C2", "Miaolingian"),
("Ca2", "Pennsylvanian"),
("O1", "Lower Ordovician"),
("O2", "Middle Ordovician"),
("J1_basal", "Jurassic"),
]

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)

        NkfOccurrence.objects.filter(source_code='6').delete()

        group_by_result = NkfOccurrence6.objects.raw('SELECT 1 as id, type_code, species, unit_code, strat_range, location_code, source, COUNT(location_code) FROM nkfcluster_nkfoccurrence6 GROUP BY type_code, species, unit_code, strat_range, location_code, source')
        for occ6 in group_by_result:
            occ1 = NkfOccurrence()
            occ1.species_name = occ6.species
            occ1.strat_unit = occ6.unit_code
            occ1.location = occ6.location_code
            occ1.group = occ6.type_code
            occ1.source = occ6.source
            occ1.source_code = '6'
            #occ1.chronounit = 
            chrono_name = ""
            for chrono in STRAT_RANGE_CHOICES:
                val, name = chrono
                if val == occ6.strat_range:
                    chrono_name = name
                    chrono_unit = ChronoUnit.objects.get(name=chrono_name)
                    if chrono_unit:
                        occ1.chronounit = chrono_unit

            occ1.process_genus_name()
            occ1.save()
            #print(occ1.species_name, occ1.location, occ1.strat_unit)