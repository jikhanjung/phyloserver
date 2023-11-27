from multiprocessing.spawn import prepare
from unittest import runner
from rose.models import RoseOccurrence
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
    help = "Customized load data"
    runner = None

    def handle(self, **options):
        print(options)

        RoseOccurrence.objects.all().delete()
        sheet_name = 'Sheet1'
        df = pd.read_excel (r'rose/data/rose_data.xlsx',sheet_name)
        print(df)

        for index, row in df.iterrows():
            print("index:", index)
            if pd.notna(row['strike']):
                occ = RoseOccurrence()
                occ.locality = row['locality']
                occ.age = row['age']
                occ.comment = row['comment']
                occ.strike = row['strike']
                occ.dip = row['dip']
                occ.save()
                print("occ:", occ)