from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, NkfOccurrence5, NkfLocality, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, ChronoUnit
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
("홍점통",""),
("신곡통","신곡주층"),
("황주계 신곡통","신곡주층"),
("고풍통","고풍주층"),
("만달통","만달주층"),
("무진통-고풍통 경계부","무진주층"),
("릉리주층 상부층","릉리주층"),
("고풍주층의 '아래층'","고풍주층"),
]

LITHOUNIT_HASH = {
"기저역암층 (송림력암층)":"송림산주층",
"부암산통":"림진군층",
"곡산통":"곡산주층",
"후기 오르도비스기 지층?":"상서주층?",
"상원계 직현통 ('독산층')":"직현군층",
"곡산통 하부":"곡산주층",
"옥로봉층":"중화주층",
"신곡주층 최하부":"신곡주층",
"림진군층 부압주층, 삭녕주층":"림진군층",
"만달주층 운학층":"만달주층",
"월양주층":"월양주층",
"림진군층 부압주층":"부압주층",
}

LOCALITY_HASH = {
"송림":"송림",
"황해북도 금천":"평산-금천",
"황해북도 신계군, 곡산군":"곡산",
"황주군 삼정리 뒷산 북쪽사면 (삼정리, 룡궁리 일대)":"황주",
"양강도 삼수군 번포리":"혜산",
"황해북도 곡산군 월양리":"곡산",
"황주":"황주",
"황주군 신상리":"황주",
"ㅇㅇ추공 767-768m 수준의 암심":"unknown",
"개성시 려현리":"평산-금천",
"승호지구":"승호-사동",
"수안군 룡현리":"수안",
"금천":"평산-금천",
}

CHRONO_HASH = {
"D1": "Lower Devonian",
"D2": "Middle Devonian",
"D3": "Upper Devonian",
"Siluro": "Silurian",
}
class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)

        NkfOccurrence5.objects.all().delete()
        sheet_name = r'220621individual articles-extra'
        df = pd.read_excel (r'nkfcluster/data/2022-05-03 화석산출 정리.xls',sheet_name)
        print(df)

        for index, row in df.iterrows():
            #print(row)
            if pd.notna(row['Title']):
                occ = NkfOccurrence5()
                occ.index = index
                occ.author1 = row['1저자'] if pd.notna(row['1저자']) else ''
                occ.author2 = row['2저자'] if pd.notna(row['2저자']) else ''
                occ.author3 = row['3저자'] if pd.notna(row['3저자']) else ''
                occ.author4 = row['4저자'] if pd.notna(row['4저자']) else ''
                occ.author_list = row['Author']
                occ.year = row['Year']
                occ.publication = row['Publication']
                occ.issue = row['Issue']
                occ.pages = row['Pages']
                occ.geologic_period = row['Geologic period']
                occ.fossil_group = row['Fossil group']
                occ.locality = row['Locality']
                occ.stratigraphy = row['Stratigraphy']
                #occ.lithology = row['Lithology']
                occ.figure = row['Figure']
                occ.implication = row['Implication']
                occ.title = row['Title']
                occ.listed_species = row['Listed species']
                #occ.note = row['Note']
                occ.note = row['Note'] if pd.notna(row['Note']) else ''
                occ.source = sheet_name

                locality = row['Locality']
                if locality in LOCALITY_HASH.keys():
                    location_name = LOCALITY_HASH[locality]

                    for choice in LOCATION_CHOICES:
                        #print(choice)
                        val, disp = choice
                        if disp == location_name:
                            print("matches!", choice,row['Locality'],location_name)
                            occ.locality_code = val
                            print("locality code:", occ.locality_code, val)
                            break

                strat_unit = row['Stratigraphy']
                if strat_unit in LITHOUNIT_HASH.keys():
                    unit_name = LITHOUNIT_HASH[strat_unit]
                    for choice in STRATUNIT_CHOICES:
                        val, disp = choice
                        if disp.upper() == unit_name.upper():
                            occ.stratigraphy_code = val
                            break

                for choice in GROUP_CHOICES:
                    val, disp = choice
                    if disp.upper() == str(row['Fossil group']).upper():
                        occ.fossil_group_code = val
                        break
                
                chronounit = row['Geologic period']
                chrono_list = chronounit.split('-')
                #print(chrono_list)
                for idx, chrono in enumerate(chrono_list):
                    if chrono in CHRONO_HASH.keys():
                        chrono_list[idx] = CHRONO_HASH[chrono]
                #print(chrono_list)

                if len(chrono_list) > 1:
                    from_name, to_name = chrono_list
                    #from_chronounit = ChronoUnit.objects.get(name=from_name)
                    occ.from_chronounit = from_name
                    occ.to_chronounit = to_name
                else:
                    
                    occ.from_chronounit = chrono_list[0]
                    occ.to_chronounit = chrono_list[0]

                lithology_found = False
                for choice in LITHOLOGY_CHOICES:
                    val, disp = choice
                    #print(row['Lithology'],disp,val)
                    if disp.upper() == row['Lithology'].upper():
                        occ.lithology = val
                        lithology_found = True
                        break
                if not lithology_found:
                    occ.lithology = ''
                
                #print(occ.from_chronounit, occ.to_chronounit)

                occ.save()
