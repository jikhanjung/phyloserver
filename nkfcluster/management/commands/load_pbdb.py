from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, NkfLocality, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, PbdbOccurrence
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

from django.db import transaction

class Command(BaseCommand):
    help = "Load PBDB"
    runner = None

    def handle(self, **options):
        print(options)


        PbdbOccurrence.objects.all().delete()

        excel_filename = r'D:/projects/phyloserver/nkfcluster/data/pbdb_data_Cambrian_Trilobite.xls'
        sheet_name = 'pbdb_data_Cambrian_Trilobite'
        df = pd.read_excel (r'nkfcluster/data/pbdb_data_Cambrian_Trilobite.xls',sheet_name)
        print(df)

        with transaction.atomic():
            for index, row in df.iterrows():
                strat_unit = ""
                lithology = ""
                group = ""
                species_name = ""
                location = ""
                
                #print( row['기관표본번호'])
                if pd.notna(row['identified_name']):
                    
                    #print(index,"Strat unit:",row['Stratigraphic unit'])
                    if row['accepted_rank'] not in ['genus','species']:
                        continue
                    if row['cc'] != 'CN':
                        continue

                    occ = PbdbOccurrence()
                    if row['identified_rank'].upper() == 'SPECIES':
                        occ.species_name = row['identified_name']
                        occ.process_genus_name()
                    elif row['identified_rank'].upper() in ['GENUS','SUBGENUS']:
                        occ.species_name = row['identified_name']
                        occ.process_genus_name()
                        occ.species_name = ''

                    if pd.notna(row['occurrence_no']):
                        occ.occno = row['occurrence_no']
                    if pd.notna(row['collection_no']):
                        occ.collno = row['collection_no']


                    if pd.notna(row['early_interval']):
                        occ.early_interval = row['early_interval']
                    if pd.notna(row['late_interval']):
                        occ.late_interval = row['late_interval']
                    if pd.notna(row['max_ma']):
                        occ.max_ma = float(row['max_ma'])
                    if pd.notna(row['min_ma']):    
                        occ.min_ma = float(row['min_ma'])
                    occ.process_chronounit()
                    occ.latitude = row['lat']
                    occ.longitude = row['lng']
                    if pd.notna(row['formation']):
                        occ.formation = row['formation']

                    if pd.notna(row['cc']):    
                        occ.country = row['cc']
                    if pd.notna(row['state']):    
                        occ.state = row['state']
                    if pd.notna(row['county']):    
                        occ.county = row['county']
                    occ.group = 'TR'
                    occ.process_region()
                    if occ.species_name == '' and occ.genus_name == '':
                        continue
                    else:
                        occ.save()

                if index == 10:
                    break
