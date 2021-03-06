from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence1, NkfOccurrence6, NkfOccurrence3, NkfOccurrence4, NkfLocality, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES
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

LOCALITY_LIST = [
    { 'name': "평남분지 남부", 'level': 1 },
    { 'name': "황주-법동향사대", 'level': 2, 'parent': "평남분지 남부" },
    { 'name': "황주-법동향사대 남부지역", 'level': 2, 'parent': "평남분지 남부" },
    { 'name': "남포", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "송림", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "황주", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "수안", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "곡산", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "법동", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "은률-과일", 'level': 3, 'parent': "황주-법동향사대 남부지역" },
    { 'name': "평산-금천", 'level': 3, 'parent': "황주-법동향사대 남부지역" },
    { 'name': "옹진-강령", 'level': 3, 'parent': "황주-법동향사대 남부지역" },
    { 'name': "연탄", 'level': 3, 'parent': "황주-법동향사대" },
    { 'name': "평남분지 북부", 'level': 1 },
    { 'name': "덕천-맹산요함대", 'level': 2, 'parent': "평남분지 북부" },
    { 'name': "덕천-맹산요함대 이외지역", 'level': 2, 'parent': "평남분지 북부" },
    { 'name': "개천-덕천-순천", 'level': 3, 'parent': "덕천-맹산요함대" },
    { 'name': "구장", 'level': 3, 'parent': "덕천-맹산요함대" },
    { 'name': "맹산", 'level': 3, 'parent': "덕천-맹산요함대" },
    { 'name': "은산", 'level': 3, 'parent': "덕천-맹산요함대" },
    { 'name': "중화-상원", 'level': 3, 'parent': "덕천-맹산요함대 이외지역" },
    { 'name': "승호-사동", 'level': 3, 'parent': "덕천-맹산요함대 이외지역" },
    { 'name': "연산-신평", 'level': 3, 'parent': "덕천-맹산요함대 이외지역" },
    { 'name': "강서-강동", 'level': 3, 'parent': "덕천-맹산요함대 이외지역" },
    { 'name': "고원-천내", 'level': 3, 'parent': "덕천-맹산요함대 이외지역" },
    { 'name': "낭림육괴(Lv.1)", 'level': 1 },
    { 'name': "낭림육괴(Lv.2)", 'level': 2, 'parent': "낭림육괴(Lv.1)" },
    { 'name': "초산-고풍", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "강계-만포", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "화평", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "전천-성간", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "장진", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "부전", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "대흥", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "신포", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
    { 'name': "혜산", 'level': 3, 'parent': "낭림육괴(Lv.2)" },
]

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
# occ4
("상원","중화-상원"),
("수안","수안"),
("중화","중화-상원"),
("황주","황주"),
("초산","초산-고풍"),
("과일","은률-과일"),
("초산, 고풍","초산-고풍"),
("사동구역","승호-사동"),
("황해북도 연탄군","연탄"),
("중강군 토성리",""),
("평산군 평화리","평산-금천"),
("평산군 평산읍","평산-금천"),
("황해북도 서흥호",""),
("자성군 연풍리",""),
("황해북도 린산군 모정","평산-금천"),
("황주군 천주리 두암산일대","황주"),
("중화군 중화읍 옥로봉지역","중화-상원"),
("연탄군 금봉리 비랑동지역","연탄"),
("연탄군 수봉리","연탄"),
("강원도 천내","고원-천내"),
("황해북도 황주군 두암산","황주"),
("황주군 운성리","황주"),
("혜산시 강구동지구","혜산"),
("혜산시 마산-강구동지구","혜산"),
("평양시 력포구역","중화-상원"),
("황주군 운성리 계암동의 동쪽에 있는 북쪽릉선","황주"),
("혜산시 강구지역","혜산"),
("양강도 혜산시 강구동","혜산"),
("황해북도 황주군 운성리 신사동","황주"),
("과일군 염전리","은률-과일"),
("과일군 북창리","은률-과일"),
("평산군 평화리, 례성리","평산-금천"),
("덕천","개천-덕천-순천"),
("황주군 두암산","황주"),
#occ6
("평안남도 북창군 원평리", "북창"),
("황해북도 황주군 외상리", "황주"),
("자강도 고풍군", "초산-고풍"),
("황해북도 수안군 주경리 목굴산", "수안"),
("황해북도 곡산군 월양리 큰굴산", "곡산"),
("황해북도 곡산군 월양리", "곡산"),
("황해북도 곡산군 송림리 아미산", "곡산"),
("황해북도 곡산군 월양리 고말산", "곡산"),
("황해북도 송림시", "송림"),
("황해북도 수안군 룡현리", "수안"),
("황해북도 신계군 해포리", "신계"),
("황해북도 곡산군 송림리", "곡산"),
("강원도 법동군 상서리", "법동"),
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
#occ4
("연탄군층 릉리주층","릉리주층"),
("림촌층","림촌주층"),
("무진통","무진주층"),
("흑교통","흑교주층"),
("심곡층","흑교주층"),
("명월리층","무진주층"),
("중화주층","중화주층"),
("상원계 사당우통",""),
("구현계 비랑동통","비랑동주층"),
("상원계 직현통 토성층",""),
("상원게 묵천통 묵천층",""),
("설화산층 (상원계 묵천통)",""),
("신곡주층","신곡주층"),
("황주군층 흑교주층","흑교주층"),
("비랑동통","비랑동주층"),
("구현계 릉리통","릉리주층"),
#("홍점통",""),
("신곡통","신곡주층"),
("황주계 신곡통","신곡주층"),
("고풍통","고풍주층"),
("만달통","만달주층"),
("무진통-고풍통 경계부","무진주층"),
("릉리주층 상부층","릉리주층"),
("고풍주층의 '아래층'","고풍주층"),
#occ6
("홍점통", "홍점통"),
("곡산통", "곡산주층"),
("송림산통 기저력암층", "송림산주층"),
("송림산통 기저력암 석회암력", "송림산주층"),
("송림산통 기저력암층의 석회암력", "송림산주층"),
("미루통", "상서주층"),
("송림산통 기저력암층 석회암력", "송림산주층"),
("Songrim basal congl. (lime)", "송림산주층"),
]

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)

        SOURCE_NK_BRACHIOPOD = '조선의 화석(완족류)'
        SOURCE_NK_CORAL = '조선의 화석(산호)'
        source_code_list = [ SOURCE_NK_BRACHIOPOD, SOURCE_NK_CORAL ]
        filename_list = [ 'North_Korean_Fossil (Brachiopod).xls', 'North_Korean_Fossil (Coral)_rev.xls' ]
        sheet_name_list = [ r'Original', r'Fossil Coral list' ]

        for i in range(2):

            NkfOccurrence6.objects.filter(source=source_code_list[i]).delete()
            df = pd.read_excel (r'nkfcluster/data/' + filename_list[i],sheet_name_list[i])
            print(df)
            not_found_location = []
            not_found_unit = []
            not_found_group = []

            for index, row in df.iterrows():
                if pd.notna(row['species']):
                    occ = NkfOccurrence6()
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
                    occ.source = source_code_list[i]

                    location_found = False
                    for loc in LOCATION_CONVERSION_TABLE:
                        val1, val2 = loc
                        if val1 == row['location']:
                            location_name = val2
                            for choice in LOCATION_CHOICES:
                                val, disp = choice
                                if disp == location_name:
                                    location_found = True
                                    occ.location_code = val
                                    break
                            break
                    if not location_found and row['location'] not in not_found_location:
                        not_found_location.append(row['location'])

                    unit_found = False
                    for unit in UNIT_CONVERSION_TABLE:
                        val1, val2 = unit
                        if val1 == row['unit']:
                            unit_name = val2
                            for choice in STRATUNIT_CHOICES:
                                val, disp = choice
                                if disp == unit_name:
                                    unit_found = True
                                    occ.unit_code = val
                                    break
                            break
                    if not unit_found and row['unit'] not in not_found_unit:
                        not_found_unit.append(row['unit'])

                    group_found = False
                    group_name = row['type']
                    for choice in GROUP_CHOICES:
                        val, disp = choice
                        if disp == group_name:
                            group_found = True
                            occ.type_code = val
                            break
                    if not group_found and row['type'] not in not_found_group:
                        not_found_group.append(row['type'])
                    occ.save()
            print("not found location for", filename_list[i], not_found_location)
            print("not found unit for", filename_list[i], not_found_unit)
            print("not found group for", filename_list[i], not_found_group)

