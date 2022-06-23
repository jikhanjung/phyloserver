from django.db import models
from django.db.models import Q

# Create your models here.
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
    ('SLS','송림산주층'),
    ('LJG','림진군층'),
    ('GS','곡산주층'),
    ('SS','상서주층'),
    ('JHG','직현군층'),
    ('WY','월양주층'),
    ('BA','부압주층'),
]

LITHOLOGY_CHOICES = [
    ('PR','phosphatic rock'),
    ('ST','siltstone'),
    ('LS','limestone'),
    ('PS','phosphatic siltstone'),
    ('SLST','slate/siltstone'),
    ('SS','sandstone'),
    ('SC','siliciclastic'),
    ('BS','Black slate'),
    ('BSLS','Black slate-limestone coupling'),
    ('SL','slate'),
    ('LSDS','limestone, dolostone'),
    ('DS','dolostone'),
    ('MS','mudstone'),
    ('PRLS','phosphatic rock, limestone'),
    ('LSSL','limestone, slate'),
    ('SLDS','slate, dolostone'),
    ('CA','carbonate rock'),
    ('QZ','Quartzite'),
]

LOCATION_CHOICES = [
    ("NP","남포"),
    ("SL","송림"),
    ("HJ","황주"),
    ("SA","수안"),
    ("GS","곡산"),
    ("BD","법동"),
    ("ERGI","은률-과일"),
    ("PSGC","평산-금천"),
    ("OJGR","옹진-강령"),
    ("JHSW","중화-상원"),
    ("SHSD","승호-사동"),
    ("YSSP","연산-신평"),
    ("GSGD","강서-강동"),
    ("GCDCSC","개천-덕천-순천"),
    ("GJ","구장"),
    ("MS","맹산"),
    ("ES","은산"),
    ("GWCN","고원-천내"),
    ("CSGP","초산-고풍"),
    ("GGMP","강계-만포"),
    ("HP","화평"),
    ("JCSG","전천-성간"),
    ("JJ","장진"),
    ("BJ","부전"),
    ("DH","대흥"),
    ("SP","신포"),
    ("HS","혜산"),
    ("TB","태백"),
    ("YT","연탄"),
]
GROUP_CHOICES = [
    ("SP","sponge"),
    ("HY","hyolith"),
    ("TR","trilobite"),
    ("BR","brachiopod"),
    ("BD","bradoriid"),
    ("AG","algae"),
    ("PR","problematic"),
    ("HC","helcionelloid"),
    ("GA","gastropod"),
    ("CE","cephalopod"),
    ("CD","conodont"),
    ("CR","crinoid"),
    ("CA","coral"),
    ("BZ","bryozoan"),
    ("OS","ostracod"),
    ("PL","plants"),
    ("TF","trace fossils"),
    ("IV","invertebrates"),
]


class ChronoUnit(models.Model):
    #CHRONOUNIT_NUMERIC_LEVEL = { 'SE': 5, 'EO': 4, 'ER': 3, 'PE': 2, 'EP': 1, 'AG': 0 }
    CHRONOUNIT_LEVEL_CHOICES = [
        ( '6', 'Supereon' ),
        ( '5', 'Eon' ),
        ( '4', 'Era' ),
        ( '3', 'Period' ),
        ( '2', 'Epoch' ),
        ( '1', 'Age' ),
    ]
    name = models.CharField(max_length=200)
    level = models.CharField(max_length=1, choices=CHRONOUNIT_LEVEL_CHOICES, blank=True)
    abbreviation = models.CharField(max_length=200, blank=True)
    begin = models.FloatField(blank=True, null=True)
    end = models.FloatField(blank=True, null=True)
    terminal_unit_count = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    created_on = models.DateTimeField(blank=True,null=True,auto_now_add=True)
    created_by = models.CharField(max_length=20,blank=True)
    modified_on = models.DateTimeField(blank=True,null=True,auto_now=True)
    modified_by = models.CharField(max_length=20,blank=True)
    #terminal_unit_count = 0

    def __str__(self):
        return self.name
    
    def get_numeric_level(self):
        return range(int(self.level)-1)
        #return self.CHRONOUNIT_NUMERIC_LEVEL[self.level]

    def get_children_count(self):
        return len(self.children)
    
    def calculate_terminal_unit_count(self):
        import logging
        logger = logging.getLogger(__name__)

        terminal_unit_count = 0
        if self.children.all():
            for child in self.children.all():
                terminal_unit_count += child.calculate_terminal_unit_count()
        else:
            terminal_unit_count = 1
        self.terminal_unit_count = terminal_unit_count
        logger.error('Something went wrong! '+str(self.id)+":"+str(terminal_unit_count))
        self.save()
        return terminal_unit_count
    class Meta:
        ordering = ["begin"]

class NkfOccurrence(models.Model):
    index = models.IntegerField(blank=True,null=True)
    strat_unit = models.CharField(max_length=10,choices=STRATUNIT_CHOICES,blank=True,null=True)
    chronounit = models.ForeignKey(ChronoUnit,on_delete=models.CASCADE,blank=True,null=True)
    lithology = models.CharField(max_length=10,choices=LITHOLOGY_CHOICES,blank=True,null=True)
    group = models.CharField(max_length=200,choices=GROUP_CHOICES,blank=True,null=True)
    species_name = models.CharField(max_length=200,blank=True,null=True)
    genus_name = models.CharField(max_length=200,blank=True,null=True)
    revised_species_name = models.CharField(max_length=200,blank=True,null=True)
    revised_genus_name = models.CharField(max_length=200,blank=True,null=True)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES,blank=True,null=True )
    source = models.CharField(max_length=200,blank=True,null=True )
    source_code = models.CharField(max_length=10,blank=True,null=True )
    def __str__(self):
        return self.species_name + " @" + self.location

    def process_genus_name(self):
        if self.species_name and self.species_name != '':
            name_list = self.species_name.split(" ")
            if len(name_list) > 0:
                self.genus_name = name_list[0]
        if self.revised_species_name and self.revised_species_name != '':
            revised_name_list = self.revised_species_name.split(" ")
            if len(revised_name_list) > 0:
                self.revised_genus_name = revised_name_list[0]

class NkfOccurrence1(models.Model):
    index = models.IntegerField(blank=True,null=True)
    strat_unit = models.CharField(max_length=10,choices=STRATUNIT_CHOICES,blank=True,null=True)
    chronounit = models.ForeignKey(ChronoUnit,on_delete=models.CASCADE,blank=True,null=True)
    lithology = models.CharField(max_length=10,choices=LITHOLOGY_CHOICES,blank=True,null=True)
    group = models.CharField(max_length=200,choices=GROUP_CHOICES,blank=True,null=True)
    species_name = models.CharField(max_length=200,blank=True,null=True)
    genus_name = models.CharField(max_length=200,blank=True,null=True)
    revised_species_name = models.CharField(max_length=200,blank=True,null=True)
    revised_genus_name = models.CharField(max_length=200,blank=True,null=True)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES,blank=True,null=True )
    source = models.CharField(max_length=200,blank=True,null=True )
    source_code = models.CharField(max_length=10,blank=True,null=True )
    def __str__(self):
        return self.species_name + " @" + self.location

    def process_genus_name(self):
        if self.species_name and self.species_name != '':
            name_list = self.species_name.split(" ")
            if len(name_list) > 0:
                self.genus_name = name_list[0]
        if self.revised_species_name and self.revised_species_name != '':
            revised_name_list = self.revised_species_name.split(" ")
            if len(revised_name_list) > 0:
                self.revised_genus_name = revised_name_list[0]

class NkfOccurrence2(models.Model):
    index = models.IntegerField(blank=True,null=True)
    type = models.CharField(max_length=200,blank=True,null=True)
    type_code = models.CharField(max_length=10,blank=True,null=True)
    plate = models.CharField(max_length=10,blank=True,null=True)
    figure = models.CharField(max_length=10,blank=True,null=True)
    species = models.CharField(max_length=100,blank=True,null=True)
    preservation = models.CharField(max_length=100,blank=True,null=True)
    preservation_eng = models.CharField(max_length=100,blank=True,null=True)
    location = models.CharField(max_length=200,blank=True,null=True)
    location_code = models.CharField(max_length=10,blank=True,null=True)
    unit = models.CharField(max_length=100,blank=True,null=True)
    unit_eng = models.CharField(max_length=100,blank=True,null=True)
    unit_code = models.CharField(max_length=10,blank=True,null=True)
    strat_range = models.CharField(max_length=100,blank=True,null=True)
    latitude = models.CharField(max_length=100,blank=True,null=True)
    longitude = models.CharField(max_length=100,blank=True,null=True)
    source = models.CharField(max_length=200,blank=True,null=True )
    def __str__(self):
        return self.species_name + " @" + self.location

class NkfOccurrence3(models.Model):
    index = models.IntegerField(blank=True,null=True)
    author = models.CharField(max_length=200,blank=True,null=True)
    year = models.CharField(max_length=10,blank=True,null=True)
    publication = models.CharField(max_length=100,blank=True,null=True)
    issue = models.CharField(max_length=10,blank=True,null=True)
    pages = models.CharField(max_length=10,blank=True,null=True)
    geologic_period = models.CharField(max_length=100,blank=True,null=True)
    fossil_group = models.CharField(max_length=100,blank=True,null=True)
    fossil_group_code = models.CharField(max_length=10,blank=True,null=True)
    locality = models.CharField(max_length=200,blank=True,null=True)
    locality_code = models.CharField(max_length=10,blank=True,null=True)
    stratigraphy = models.CharField(max_length=100,blank=True,null=True)
    stratigraphy_code = models.CharField(max_length=10,blank=True,null=True)
    lithology = models.CharField(max_length=100,blank=True,null=True)
    figure = models.CharField(max_length=100,blank=True,null=True)
    implication = models.CharField(max_length=100,blank=True,null=True)
    title = models.CharField(max_length=500,blank=True,null=True)
    listed_name = models.CharField(max_length=500,blank=True,null=True )
    note = models.CharField(max_length=500,blank=True,null=True )
    def __str__(self):
        return self.title


class NkfOccurrence4(models.Model):
    index = models.IntegerField(blank=True,null=True)
    author1 = models.CharField(max_length=200,blank=True,null=True)
    author2 = models.CharField(max_length=200,blank=True,null=True)
    author3 = models.CharField(max_length=200,blank=True,null=True)
    author4 = models.CharField(max_length=200,blank=True,null=True)
    author_list = models.CharField(max_length=200,blank=True,null=True)
    year = models.CharField(max_length=10,blank=True,null=True)
    publication = models.CharField(max_length=100,blank=True,null=True)
    issue = models.CharField(max_length=10,blank=True,null=True)
    pages = models.CharField(max_length=10,blank=True,null=True)
    geologic_period = models.CharField(max_length=100,blank=True,null=True)
    fossil_group = models.CharField(max_length=100,blank=True,null=True)
    fossil_group_code = models.CharField(max_length=10,blank=True,null=True)
    locality = models.CharField(max_length=200,blank=True,null=True)
    locality_code = models.CharField(max_length=10,blank=True,null=True)
    stratigraphy = models.CharField(max_length=100,blank=True,null=True)
    stratigraphy_code = models.CharField(max_length=10,blank=True,null=True)
    lithology = models.CharField(max_length=100,blank=True,null=True)
    figure = models.CharField(max_length=100,blank=True,null=True)
    implication = models.CharField(max_length=100,blank=True,null=True)
    title = models.CharField(max_length=500,blank=True,null=True)
    listed_species = models.CharField(max_length=500,blank=True,null=True )
    note = models.CharField(max_length=500,blank=True,null=True )
    def __str__(self):
        return self.title

class NkfOccurrence5(models.Model):
    index = models.IntegerField(blank=True,null=True)
    author1 = models.CharField(max_length=200,blank=True,null=True)
    author2 = models.CharField(max_length=200,blank=True,null=True)
    author3 = models.CharField(max_length=200,blank=True,null=True)
    author4 = models.CharField(max_length=200,blank=True,null=True)
    author_list = models.CharField(max_length=200,blank=True,null=True)
    year = models.CharField(max_length=10,blank=True,null=True)
    publication = models.CharField(max_length=100,blank=True,null=True)
    issue = models.CharField(max_length=10,blank=True,null=True)
    pages = models.CharField(max_length=10,blank=True,null=True)
    geologic_period = models.CharField(max_length=100,blank=True,null=True)
    from_chronounit = models.CharField(max_length=100,blank=True,null=True)
    to_chronounit = models.CharField(max_length=100,blank=True,null=True)
    fossil_group = models.CharField(max_length=100,blank=True,null=True)
    fossil_group_code = models.CharField(max_length=10,blank=True,null=True)
    locality = models.CharField(max_length=200,blank=True,null=True)
    locality_code = models.CharField(max_length=10,blank=True,null=True)
    stratigraphy = models.CharField(max_length=100,blank=True,null=True)
    stratigraphy_code = models.CharField(max_length=10,blank=True,null=True)
    lithology = models.CharField(max_length=100,choices=LITHOLOGY_CHOICES,blank=True,null=True)
    figure = models.CharField(max_length=100,blank=True,null=True)
    implication = models.CharField(max_length=100,blank=True,null=True)
    title = models.CharField(max_length=500,blank=True,null=True)
    listed_species = models.CharField(max_length=500,blank=True,null=True )
    note = models.CharField(max_length=500,blank=True,null=True )
    def __str__(self):
        return self.title

class NkfLocality(models.Model):
    index = models.IntegerField(blank=True,null=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    level = models.IntegerField(blank=True,null=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True,related_name='children')

    def __str__(self):
        return self.name

CHINA_REGION_HASH ={
"CN-Anhui-Chuxian":"SC",
"CN-Anhui-Huainan":"NC",
"CN-Anhui-Jing Xian":"SC",
"CN-Anhui-Jingxian":"SC",
"CN-Chongqing-Chengkou":"SC",
"CN-Chongqing-Youyang":"SC",
"CN-Gansu-":"Other",
"CN-Guangxi-":"SC",
"CN-Guangxi-Jingxi":"SC",
"CN-Guannxi-":"SC",
"CN-Guizhou-":"SC",
"CN-Guizhou-Danzhai":"SC",
"CN-Guizhou-Fuquan":"SC",
"CN-Guizhou-Jianhe":"SC",
"CN-Guizhou-Jinsha":"SC",
"CN-Guizhou-Kaiyang":"SC",
"CN-Guizhou-Meitan":"SC",
"CN-Guizhou-Songtao":"SC",
"CN-Guizhou-Taijiang":"SC",
"CN-Guizhou-Tongren":"SC",
"CN-Guizhou-Wanshan":"SC",
"CN-Guizhou-Weng'an":"SC",
"CN-Guizhou-Yuping":"SC",
"CN-Guizhou-Yuqing":"SC",
"CN-Guizhou-Zhenyuan":"SC",
"CN-Guizhou-Zunyi":"SC",
"CN-Hebei-Tangshan":"NC",
"CN-Henan-Dengfeng":"NC",
"CN-Henan-Jixian":"NC",
"CN-Henan-Linru":"NC",
"CN-Henan-Linxian":"NC",
"CN-Henan-Lushan":"NC",
"CN-Henan-Mianchi":"NC",
"CN-Henan-Ruzhou":"NC",
"CN-Henan-Xichuan":"SC",
"CN-Henan-Ye Xian":"BELT",
"CN-Hubai-":"SC",
"CN-Hubei-":"SC",
"CN-Hubei-Changyang":"SC",
"CN-Hubei-Chongyang":"SC",
"CN-Hubei-Junxian":"SC",
"CN-Hubei-Yichang":"SC",
"CN-Hubei-Zhuxi":"SC",
"CN-Hunan-":"SC",
"CN-Hunan-Cili":"SC",
"CN-Hunan-Fenghuang":"SC",
"CN-Hunan-Guzhang":"SC",
"CN-Hunan-Longshan":"SC",
"CN-Hunan-Taoyuan":"SC",
"CN-Hunan-Zhijiang":"SC",
"CN-Jiangsu-Jiawang":"SC",
"CN-Jiangsu-Kunshan":"SC",
"CN-Jiangsu-Luhe":"SC",
"CN-Jilin-":"NC",
"CN-Jilin Provence-":"NC",
"CN-Liaoning-Benxi":"NC",
"CN-Liaoning-Liaoyang":"NC",
"CN-Liaoning-Wafangdian":"NC",
"CN-Nei Mongol-":"OTHER",
"CN-Nei Mongol-Qingshuihe":"OTHER",
"CN-Ningxia-":"NC",
"CN-Qinghai-":"OTHER",
"CN-Shaanxi-":"",
"CN-Shaanxi-Longxian":"NC",
"CN-Shaanxi-Luonan":"NC",
"CN-Shaanxi-Mianxian":"SC",
"CN-Shaanxi-Nanzheng":"SC",
"CN-Shaanxi-Ningqiang":"SC",
"CN-Shaanxi-Shangnan":"SC",
"CN-Shaanxi-Zhenba":"SC",
"CN-Shandong-":"NC",
"CN-Shandong-Changqing":"NC",
"CN-Shandong-Laiwu":"NC",
"CN-Shandong-Xintai":"NC",
"CN-Shanghai-Baoshan":"SC",
"CN-Shanxi-":"NC",
"CN-Shanxi-Pinglu":"NC",
"CN-Shanxi-Ruicheng":"NC",
"CN-Shanxi-Xixian":"NC",
"CN-Sichuan-Emei":"SC",
"CN-Sichuan-Leshan":"SC",
"CN-Sichuan-Nanjiang":"SC",
"CN-Sichuan-Wanyuan":"SC",
"CN-Xinjiang-":"OTHER",
"CN-Yunnan-":"SC",
"CN-Yunnan-Anning":"SC",
"CN-Yunnan-Chengjiang":"SC",
"CN-Yunnan-Fumin":"SC",
"CN-Yunnan-Funing":"SC",
"CN-Yunnan-Haikou":"SC",
"CN-Yunnan-Jinning":"SC",
"CN-Yunnan-Kunming":"SC",
"CN-Yunnan-Malong":"SC",
"CN-Yunnan-Wuding":"SC",
"CN-Yunnan-Yiliang":"SC",
"CN-Yunnan-Zhongdian":"SC",
"CN-Zhejiang-":"SC",
"CN-Zhejiang-Changshan":"SC",
"CN-Zhejiang-Jiangshan":"SC",
}
class PbdbOccurrence(models.Model):
    occno = models.CharField(max_length=50,blank=True,null=True,verbose_name="PBDB OccurrenceNo")
    collno = models.CharField(max_length=50,blank=True,null=True,verbose_name="PBDB CollectionNo")
    species_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="종명")
    genus_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="속명")
    revised_species_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="Revised 종명")
    revised_genus_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="Revised 속명")
    group = models.CharField(max_length=10,choices=GROUP_CHOICES,blank=True,null=True)
    early_interval = models.CharField(max_length=100,blank=True,null=True,verbose_name="From")
    late_interval = models.CharField(max_length=100,blank=True,null=True,verbose_name="To")
    max_ma = models.FloatField(blank=True,null=True,verbose_name="From Ma")
    min_ma = models.FloatField(blank=True,null=True,verbose_name="To Ma")
    chrono_from = models.ForeignKey(ChronoUnit,on_delete=models.CASCADE,blank=True,null=True,verbose_name="Chrono From",related_name='ChronoFrom')
    chrono_to = models.ForeignKey(ChronoUnit,on_delete=models.CASCADE,blank=True,null=True,verbose_name="Chrono To",related_name='ChronoTo')
    chrono_list = models.CharField(max_length=200,blank=True,null=True,verbose_name="시대")
    latitude = models.CharField(max_length=20,blank=True,null=True,verbose_name="경도")
    longitude = models.CharField(max_length=20,blank=True,null=True,verbose_name="위도")
    country = models.CharField(max_length=10,blank=True,null=True,verbose_name="국가")
    state = models.CharField(max_length=100,blank=True,null=True,verbose_name="State")
    county = models.CharField(max_length=100,blank=True,null=True,verbose_name="County")
    region = models.CharField(max_length=100,blank=True,null=True,verbose_name="Region")
    formation = models.CharField(max_length=100,blank=True,null=True)
    remarks = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.species_name + "@" + self.state

    def process_genus_name(self):
        #if self.species_name and self.species_name != '':
        #    name_list = self.species_name.split(" ")
        #    if len(name_list) > 0:
        #        self.genus_name = name_list[0]
        if self.revised_species_name and self.revised_species_name != '':
            revised_name_list = self.revised_species_name.split(" ")
            if len(revised_name_list) > 0:
                self.revised_genus_name = revised_name_list[0]

    def process_region(self):
        #print(self.country, self.state, self.county )
        region_key = "-".join([ self.country or '', self.state or '', self.county or '' ])
        region_value = ''
        if region_key in CHINA_REGION_HASH.keys():
            region_value = CHINA_REGION_HASH[region_key]
        if region_key.find('CN-Jilin') > -1:
            if self.formation and self.formation.upper().find('FENGSHAN') > -1:
                region_value = 'NC'
        if region_key == ('CN-Yunnan-'):
            region_value = ''
        self.region = region_value

    def process_chronounit(self):
        min_ma = 0
        max_ma = 0
        if self.max_ma and self.max_ma != '':
            max_ma = self.max_ma
        if self.min_ma and self.min_ma != '':
            min_ma = self.min_ma
        print(min_ma, max_ma, self.min_ma, self.max_ma)
        #chrono_list = ChronoUnit.objects.filter((Q(begin__gte=max_ma)|Q(end__lte=min_ma))&Q(level='2')).order_by('level','begin')
        qs = ChronoUnit.objects.filter(
            (   
                Q(begin__lt=max_ma)&Q(begin__gt=min_ma) |   
                Q(end__lt=max_ma)&Q(end__gt=min_ma) |   
                (   
                    Q(begin__gte=max_ma)&Q(end__lte=min_ma)
                )
            )
            &Q(level='2')
        ).order_by('level','-begin')
        print(qs)

        chrono_list = [ q for q in qs ]
        print(chrono_list)
        for chrono in chrono_list:
            print(chrono.name, chrono.begin, chrono.end)
        
        self.chrono_from = chrono_list[0]
        self.chrono_to = chrono_list[-1]

        chrononame_list = ", ".join([ c.name for c in chrono_list ])
        self.chrono_list = chrononame_list
        print(self.chrono_list)


        #self.chrono_from = min_unit
        #self.chrono_to = min_unit

class TotalOccurrence(models.Model):
    country = models.CharField(max_length=10, blank=True,null=True )
    group = models.CharField(max_length=200,choices=GROUP_CHOICES,blank=True,null=True)
    species_name = models.CharField(max_length=200,blank=True,null=True)
    genus_name = models.CharField(max_length=200,blank=True,null=True)
    locality_lvl1 = models.CharField(max_length=20, blank=True,null=True )
    locality_lvl2 = models.CharField(max_length=20, blank=True,null=True )
    locality_lvl3 = models.CharField(max_length=20, blank=True,null=True )
    chrono_lvl1 = models.CharField(max_length=20, blank=True,null=True )
    chrono_lvl2 = models.CharField(max_length=20, blank=True,null=True )
    source = models.CharField(max_length=200,blank=True,null=True )
    def __str__(self):
        return self.species_name 
