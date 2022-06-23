from nkfcluster.models import ChronoUnit, NkfOccurrence
from django.db.models import Q

from django.core.management.base import BaseCommand
import json
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype


class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        print("load chronounit")

        
        occ_list = NkfOccurrence.objects.all()

        for occ in occ_list:
            source_code = occ.source_code
            source = occ.source
            if source_code == '5':
                continue
            if source == '220426 조선지질총서2':
                occ.source_code = '1'
            elif source == '220321 김덕성 조선의화석 삼엽충':
                occ.source_code = '2'
            else:
                occ.source_code = '4'
            occ.save()