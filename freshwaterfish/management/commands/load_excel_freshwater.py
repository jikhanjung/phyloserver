from multiprocessing.spawn import prepare
from unittest import runner
from freshwaterfish.models import FrOccurrence
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

        FrOccurrence.objects.all().delete()
        sheet_name = 'Sheet1'
        df = pd.read_excel (r'freshwaterfish/data/freshwater_fish_data.xlsx',sheet_name)
        print(df)

        for index, row in df.iterrows():
            print("index:", index, row['genus'])
            if pd.notna(row['genus']):
                occ = FrOccurrence()
                occ.locality = row['locality']
                occ.country = row['country']
                occ.clade = row['clade']
                occ.family = row['family']
                occ.genus = row['genus']
                occ.origin = row['origin']
                occ.epoch = row['epoch']
                occ.age = row['age']
                occ.environment = row['environment']
                occ.continent = row['continent']
                occ.period = row['period']
                occ.save()
                print("occ:", occ)
