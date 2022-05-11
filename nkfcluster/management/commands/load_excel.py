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

LOCATION_CONVERSION_TABLE = [
("자강도 초산군 구평리","초산-고풍"),
("자강도 초산군 화건리","초산-고풍"),
("평양시 중화군 중화읍 봉화봉","중화-상원"),
("초산군 구평리","초산-고풍"),
("고풍군 문덕리","초산-고풍"),
("황해북도 황주군 천주리","황주"),
("황해북도 황주군 흑교리","황주"),
("평양시 중화군 중화읍","중화-상원"),
("자강도 장강군 종포리","강계-만포"),
("평양시 중화군 마장리","중화-상원"),
("평양시 사동구역 송신1동","승호-사동"),
("중화군 중화읍","중화-상원"),
("자강도 고풍군 고풍읍","초산-고풍"),
("평양시 중화군 흑교리","중화-상원"),
("황해남도 과일군 염전리","은률-과일"),
("황해북도 황주군 신상리","황주"),
("황해남도 과일군","은률-과일"),
("황해북도 황주군","황주"),
("평양시 승호구역 화천동","승호-사동"),
("황해남도 황주군 천주리","황주"),
("자강도 화평군 중흥구 ","화평"),
("자강도 화평군 소북리","화평"),
("평양시 중화군 중화읍 ","중화-상원"),
("자강도 초산군 가락봉","초산-고풍"),
("자강도 고풍군 문덕리","초산-고풍"),
("자강도 화평군 중흥구","화평"),
("자강도 고풍군 신창리","초산-고풍"),
("평양시 사동구역 소룡1동","승호-사동"),
("자강도 초산군 초산읍","초산-고풍"),
("평양시 중화군 봉화봉","중화-상원"),
("평양시 중화군 명월리","중화-상원"),
("자강도 초산군 구평리 수리봉","초산-고풍"),
("자강도 초산군 수리봉","초산-고풍"),
("함경남도 고원군 성내리","고원-천내"),
("평양시 승호구역 광정리","승호-사동"),
("평안남도 덕천시","개천-덕천-순천"),
("평안남도 순천시 은산","개천-덕천-순천"),
]

UNIT_CONVERSION_TABLE = [
("림촌층","림촌주층"),
("캄브리아기상세 하부층준","고풍주층"),
("마산동층","고풍주층"),
("봉화봉층","흑교주층"),
("명월리층","무진주층"),
("흑교리 기저층","평산주층"),
("옥로봉층","중화주층"),
("강로리층","중화주층"),
("연두봉층","중화주층"),
("흑교통","흑교주층"),
("사곡층(옥로봉층)","중화주층"),
("심곡층","흑교주층"),
("천주리층","중화주층"),
("흑교통(심곡통)","흑교주층"),
("운학층","만달주층"),
("성내층","신곡주층"),
("월악동층","중화주층"),
("모봉층(봉화봉층)","흑교주층"),
("월악동층(봉화봉층)","중화주층"),
("월악동층(천주리층)","중화주층"),
("림촌층?","림촌주층"),
("룡산동층","고풍주층"),
("흑교통 하부","흑교주층"),
("명월리층?","무진주층"),
("수리봉층","고풍주층"),
("신곡통","신곡주층"),
("고풍통","고풍주층"),
("신창리층","신곡주층"),
]

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)


        NkfOccurrence.objects.all().delete()
        NkfOccurrence2.objects.all().delete()
        NkfOccurrence3.objects.all().delete()

        excel_filename = r'D:/projects/phyloserver/nkfcluster/data/2022-05-03 화석산출 정리.xls'
        sheet_name = '220426 조선지질총서2'
        df = pd.read_excel (r'nkfcluster/data/2022-05-03 화석산출 정리.xls',sheet_name)
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
                        occ.source = sheet_name
                        occ.process_genus_name()
                        #print(occ)
                        occ.save()

        sheet_name = r'220321 김덕성 조선의화석 삼엽충'
        df = pd.read_excel (r'nkfcluster/data/2022-05-03 화석산출 정리.xls',sheet_name)
        print(df)

        for index, row in df.iterrows():
            if pd.notna(row['species']):
                occ = NkfOccurrence2()
                occ.index = index
                occ.type = row['type']
                occ.plate = row['plate']
                occ.figure = row['figure']
                occ.species = row['species']
                occ.preservation = row['preservation']
                occ.preservation_eng = row['preservation_eng']
                occ.location = row['location']
                occ.unit = row['unit']
                occ.unit_eng = row['unit_eng']
                occ.strat_range = row['strat_range']
                occ.latitude = row['lat']
                occ.longitude = row['lon']
                occ.source = sheet_name

                for loc in LOCATION_CONVERSION_TABLE:
                    val1, val2 = loc
                    if val1 == row['location']:
                        location_name = val2
                        for choice in LOCATION_CHOICES:
                            val, disp = choice
                            if disp == location_name:
                                occ.location_code = val
                                break
                        break

                for unit in UNIT_CONVERSION_TABLE:
                    val1, val2 = unit
                    if val1 == row['unit']:
                        unit_name = val2
                        for choice in STRATUNIT_CHOICES:
                            val, disp = choice
                            if disp == unit_name:
                                occ.unit_code = val
                                break
                        break
                for choice in GROUP_CHOICES:
                    val, disp = choice
                    if disp == row['type']:
                        occ.type_code = val
                        break

                occ.save()


        sheet_name = r'220503 individual articles'
        df = pd.read_excel (r'nkfcluster/data/2022-05-03 화석산출 정리.xls',sheet_name)
        print(df)

        for index, row in df.iterrows():
            #print(row)
            if pd.notna(row['Title']):
                occ = NkfOccurrence3()
                occ.index = index
                occ.author = row['Author']
                occ.year = row['Year']
                occ.publication = row['Publication']
                occ.issue = row['Issue']
                occ.pages = row['Pages']
                occ.geologic_period = row['Geologic period']
                occ.fossil_group = row['Fossil group']
                occ.locality = row['Locality']
                occ.stratigraphy = row['Stratigraphy']
                occ.lithology = row['Lithology']
                occ.figure = row['Figure']
                occ.implication = row['Implication']
                occ.title = row['Title']
                occ.listed_name = row['Listed name (genus)']
                occ.note = row['Note']
                occ.source = sheet_name
                occ.save()
