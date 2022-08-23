from nkfcluster.models import ChronoUnit, NkfOccurrence
from django.db.models import Q

from django.core.management.base import BaseCommand
import json
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype

ref_eng_list = [
["220426 조선지질총서2", "Pak et al. (2009)"],
["220321 김덕성 조선의화석 삼엽충", "Kim et al. (1987)"],
["김기영(1972:2)", "Kim (1972)"],
["김덕성(1973:5)", "Kim (1973)"],
["김덕성(1977:4)", "Kim (1977)"],
["김덕성(1984:4)", "Kim (1984a)"],
["김덕성(1984:5)", "Kim (1984b)"],
["리선국(2011:10)", "Ri (2011)"],
["리철준 김철수 김철근 서광식(2008:9)", "Ri et al. (2008)"],
["배용준 홍성권 리현수(1991:12)", "Pae et al. (1991)"],
["배용준 홍성권 원철국(1991:8)", "Pae et al. (1991)"],
["원철국조성복(2004:1)", "Won and Cho (2004)"],
["원철국조성복(2005:1)", "Won and Cho (2005)"],
["원철국조성복(2005:1)", "Won and Cho (2005)"],
["원철국(1997:11)", "Won (1997)"],
["원철국(2003:1)", "Won (2003)"],
["원철국 서광식(2020:3)", "Won and So (2020)"],
["원철국 송진혁(2021:1)", "Won and Song (2021)"],
["원철국 홍성권(1998:6)", "Won and Hong (1998)"],
["정창복(1972:5)", "Jong (1972)"],
["홍성권 원철국 리정임(1991:6)", "Hong et al. (1991)"],
["홍성권 원철국 하종철(1994:1)", "Hong et al. (1994)"],
["Yabe Sugiyama (1930a: 14)", "Yabe and Sugiyama (1930a)"],
["Yabe Sugiyama (1930b: 8)", "Yabe and Sugiyama (1930b)"],
["Sugiyama (1941: 8)", "Sugiyana (1941)"],
["김명학 림동수 (2011)", "Kim and Rim (2011)"],
["강준철 서광식(2011:5)", "Kang and So (2011)"],
["강준철 장덕성(2011:8)", "Kang and Jang (2011)"],
["김덕성 리상도(1989:6)", "Kim and Li (1989)"],
["김덕성 리상도(1993:4)", "Kim and Li (1993)"],
["김덕성 리상도(1995:2)", "Kim and Li (1995)"],
["김준철 서광식 원철국(2015:4)", "Kim et al. (2015)"],
["김철수 리철준 서광식(2008:7)", "Kim et al. (2008)"],
["리상도 박영철(1994:5)", "Ri and Pak (1994)"],
["리상도 박영철(1999:1)", "Ri and Pak (1999)"],
["리상도 박영철(2000:9)", "Ri and Pak (2000)"],
["리은빛(2019:6)", "Ri (2019)"],
["박영철 리현수(2003:6)", "Pak and Ri (2003)"],
["박영철 서광식(2005:3)", "Pak and So (2005)"],
["박영철 서광식 배봉하(2005:4)", "Pak et al. (2005)"],
["서광식(2010:4)", "So (2010)"],
["서광식 원철국 김혜성(2014:11)", "So et al. (2014)"],
["장덕성 김철근(2004:6)", "Jang and Kim (2004)"],
["장덕성 김철근 배봉하(2005:10)", "Jang et al. (2005)"],
["장덕성 배봉하(2007:9)", "Jang and Pae (2007)"],
["장덕성 배봉하(2007:9)", "Jang and Pae (2007)"],
["장덕성 서광식(2006:4)", "Jang and So (2006)"],
["박용선(1966:2)", "Pak (1966a)"],
["박용선(1966:3)", "Pak (1966b)"],
["박용선(1967:1)", "Pak (1967)"],
["박용선(1976:2)", "Pak (1976)"],
["박용선 강진건(1984:5)", "Pak and Kang (1984a)"],
["박용선 강진건(1984:2)", "Pak and Kang (1984b)"],
["홍성권 리정임(1990:1)", "Hong and Ri (1990)"],
["장일남 리현수 강진건(1994:8)", "Jang et al. (1994)"],
["정호상 홍성권 원철국(2001:6)", "Jong et al. (2001)"],
["정호상 홍성권 원철국(2001:6)", "Jong et al. (2001)"],
["김광룡(2011:9)", "Kim (2011)"],
["원철국김광룡(2005:3)", "Won and Kim (2005)"],
["차명도(2011:6)", "Cha (2011)"],
["강진건(2012:5)", "Kang (2012)"],
["김병성(2013:3)", "Kim (2013)"],
["김현철 서광식 원철국(2015:2)", "Kim et al. (2015)"],
["강진건(2016:4)", "Kang (2016)"],
["조선의 화석(완족류)", "Kim et al. (1987)"],
["조선의 화석(산호)", "Kim et al. (1987)"],
]

class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        print("fill english reference")

        
        occ_list = NkfOccurrence.objects.all()

        for occ in occ_list:
            ref_name = occ.source
            for ref in ref_eng_list:
                if ref[0] == ref_name:
                    occ.source_eng = ref[1]
                    occ.save()
                    break