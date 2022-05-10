from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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


        excel_filename = r'D:/projects/phyloserver/nkfcluster/data/2022-05-03 화석산출 정리.xls'

        df = pd.read_excel (r'nkfcluster/data/2022-05-03 화석산출 정리.xls',r'220426 조선지질총서2')
        print(df)

        for index, row in df.iterrows():
            strat_unit = ""
            lithology = ""
            group = ""
            species_name = ""
            location = ""
            
            #print( row['기관표본번호'])
            if pd.notna(row['Species name']):
                
                #print(index,"Strat unit:",row['Stratigraphic unit'])
                for choice in STRATUNIT_CHOICES:
                    val, disp = choice
                    if disp == row['Stratigraphic unit']:
                        strat_unit = val
                        break
                    
                for choice in LITHOLOGY_CHOICES:
                    val, disp = choice
                    if disp == row['Lithology']:
                        lithology = val
                        break
                for choice in GROUP_CHOICES:
                    val, disp = choice
                    if disp == row['Fossil group']:
                        group = val
                        break
                species_name = row['Species name']
                #print(occ)
                #print(row)
                for choice in LOCATION_CHOICES:
                    #print(choice)
                    val, disp = choice
                    if pd.notna(row[disp]):
                        #print(disp,row[disp])
                        occ = NkfOccurrence()
                        occ.strat_unit = strat_unit
                        occ.lithology = lithology
                        if lithology == '':
                            print("can't find lithology", row['Lithology'])
                            #occ.lithology = row['Lithology']
                        occ.index = index
                        occ.group = group
                        occ.species_name = species_name
                        occ.location = val
                        #print(occ)
                        occ.save()


