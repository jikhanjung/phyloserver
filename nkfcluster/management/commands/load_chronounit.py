from nkfcluster.models import ChronoUnit
from django.db.models import Q

from django.core.management.base import BaseCommand
import json
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype

class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        print("load chronounit")

        
        ChronoUnit.objects.all().delete()
        filename = "nkfcluster/data/chronounit.xls"
        sheetname = 'chronounit'
        df = pd.read_excel (filename, sheetname)
        print(df)
        for index, row in df.iterrows():
            strat_unit = ""
            lithology = ""
            group = ""
            species_name = ""
            location = ""
            
            #print( row['기관표본번호'])
            if pd.notna(row['name']):
                chronounit = ChronoUnit()
                chronounit.id = row['id']
                chronounit.name = row['name']
                chronounit.level = row['level']
                chronounit.abbreviation = row['abbreviation']
                chronounit.begin = row['begin']
                chronounit.end = row['end']
                chronounit.parent = None
                if pd.notna(row['parent']):
                    chronounit.parent = ChronoUnit.objects.get(pk=row['parent'])
                chronounit.save()



