from multiprocessing.spawn import prepare
from unittest import runner
from nkfcluster.models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, STRATUNIT_CHOICES, LITHOLOGY_CHOICES, GROUP_CHOICES, LOCATION_CHOICES, ChronoUnit
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
from django.db.models import Q

LITHOUNIT_HASH = {
"연탄군층 릉리주층":"릉리주층",
"림촌층":"림촌주층",
"무진통":"무진주층",
"흑교통":"흑교주층",
"심곡층":"흑교주층",
"명월리층":"무진주층",
"중화주층":"중화주층",
"상원계 사당우통":"사당우주층",
"구현계 비랑동통":"비랑동주층",
"상원계 직현통 토성층":"직현주층",
"상원게 묵천통 묵천층":"묵천층",
"설화산층 (상원계 묵천통)":"묵천주층",
"신곡주층":"신곡주층",
"황주군층 흑교주층":"흑교주층",
"비랑동통":"비랑동주층",
"구현계 릉리통":"릉리주층",
"홍점통":"홍점통",
"신곡통":"신곡주층",
"황주계 신곡통":"신곡주층",
"고풍통":"고풍주층",
"만달통":"만달주층",
"무진통-고풍통 경계부":"무진주층",
"릉리주층 상부층":"릉리주층",
}

LOCALITY_HASH = {
"황해북도 연탄군":"연탄",
"중강군 토성리":"중강",
"평산군 평화리":"평산-금천",
"평산군 평산읍":"평산-금천",
"황해북도 서흥호":"평산-금천",
"자성군 연풍리":"화평",
"황해북도 린산군 모정":"평산-금천",
"황주군 천주리 두암산일대":"황주",
"중화군 중화읍 옥로봉지역":"중화-상원",
"연탄군 금봉리 비랑동지역":"연탄",
"연탄군 수봉리":"연탄",
"강원도 천내":"고원-천내",
"황해북도 황주군 두암산":"황주",
"황주군 운성리":"황주",
"혜산시 강구동지구":"혜산",
"혜산시 마산-강구동지구":"혜산",
"평양시 력포구역":"중화-상원",
}
class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        print(options)
        NkfOccurrence.objects.filter(Q(source_code='4')&Q(chronounit__name='Neoproterozoic')).delete()

        occ_list = NkfOccurrence4.objects.all()
        #print(len(occ3_list))
        for occ4 in occ_list:
            if occ4.geologic_period != "Neoproterozoic":
                continue
            #print(occ3.listed_name)
            occ = NkfOccurrence()
            occ.index = occ4.index
            if occ4.stratigraphy.find('상원게') > -1:
                occ4.stratigraphy = occ4.stratigraphy.replace('상원게','상원계')
                occ4.save()
            occ.strat_unit = occ4.stratigraphy_code
            if not occ.strat_unit or occ.strat_unit == '':
                if occ4.stratigraphy in LITHOUNIT_HASH.keys():
                    strat_name = LITHOUNIT_HASH[occ4.stratigraphy]
                    for choice in STRATUNIT_CHOICES:
                        val, disp = choice
                        if disp == strat_name:
                            occ4.stratigraphy_code = val
                            occ4.save()
                            occ.strat_unit = val
                            break
            occ.location = occ4.locality_code
            if not occ.location or occ.location == '':
               if occ4.locality in LOCALITY_HASH.keys():
                    loc_name = LOCALITY_HASH[occ4.locality]
                    for choice in LOCATION_CHOICES:
                        val, disp = choice
                        if disp == loc_name:
                            occ4.locality_code = val
                            occ4.save()
                            occ.locatoin = val
                            break
 
            occ.group = occ4.fossil_group_code
            if not occ.group or occ.group == '':
                for choice in GROUP_CHOICES:
                    val, disp = choice
                    #print(val,disp,occ4.fossil_group)
                    if str(occ4.fossil_group).upper().find(disp.upper()) > -1:
                        occ.group = val
                        occ4.fossil_group_code = val
                        occ4.save()
                        break
            occ.species_name = occ4.listed_species
            occ.process_genus_name()
            occ.source = occ4.author_list + "(" + occ4.year + ":" + occ4.issue + ")"
            occ.source_code = '4'
            chrono_unit = ChronoUnit.objects.get(name=occ4.geologic_period)
            if chrono_unit:
                occ.chronounit = chrono_unit
            occ.save()

