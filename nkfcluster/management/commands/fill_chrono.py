from nkfcluster.models import ChronoUnit, NkfOccurrence
from django.db.models import Q

from django.core.management.base import BaseCommand
import json
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype

STRATUNIT_CHOICES = [
    ('PS','평산주층'),
    ('JH','중화주층'),
    ('HG','흑교주층'),
    ('LC','림촌주층'),
    ('MJ','무진주층'),
    ('GP','고풍주층'),
    ('SG','신곡주층'),
    ('MD','만달주층'),
    ('BRD','비랑동주층'),
]

STRAT_CHRONO_HASH = {
    'PS':'Series 2',
    'JH':'Series 2',
    'HG':'Miaolingian',
    'LC':'Miaolingian',
    'MJ':'Miaolingian',
    'GP':'Furongian',
    'SG':'Lower Ordovician',
    'MD':'Middle Ordovician',
}


class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        print("load chronounit")

        
        occ_list = NkfOccurrence.objects.all()

        for occ in occ_list:
            litho_code = occ.strat_unit
            if litho_code in STRAT_CHRONO_HASH.keys():
                chrono_name = STRAT_CHRONO_HASH[litho_code]
                chrono_unit = ChronoUnit.objects.get(name=chrono_name)
                if chrono_unit:
                    occ.chronounit = chrono_unit
                    #print(occ.chronounit)
                    occ.save()