from django.db import models

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
    ("BZ","bryozoan"),
]

class NkfOccurrence(models.Model):
    index = models.IntegerField(blank=True,null=True)
    strat_unit = models.CharField(max_length=10,choices=STRATUNIT_CHOICES,blank=True,null=True)
    lithology = models.CharField(max_length=10,choices=LITHOLOGY_CHOICES,blank=True,null=True)
    group = models.CharField(max_length=200,choices=GROUP_CHOICES,blank=True,null=True)
    species_name = models.CharField(max_length=200,blank=True,null=True)
    genus_name = models.CharField(max_length=200,blank=True,null=True)
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES,blank=True,null=True )
    source = models.CharField(max_length=200,blank=True,null=True )
    def __str__(self):
        return self.species_name + " @" + self.location

    def process_genus_name(self):
        name_list = self.species_name.split(" ")
        if len(name_list) > 0:
            self.genus_name = name_list[0]

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


class NkfLocality(models.Model):
    index = models.IntegerField(blank=True,null=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    level = models.IntegerField(blank=True,null=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True,related_name='children')

    def __str__(self):
        return self.name


class PbdbOccurrence(models.Model):
    occno = models.CharField(max_length=50,blank=True,null=True,verbose_name="PBDB OccurrenceNo")
    collno = models.CharField(max_length=50,blank=True,null=True,verbose_name="PBDB CollectionNo")
    species_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="종명")
    genus_name = models.CharField(max_length=200,blank=True,null=True,verbose_name="속명")
    group = models.CharField(max_length=10,choices=GROUP_CHOICES,blank=True,null=True)
    early_interval = models.CharField(max_length=100,blank=True,null=True,verbose_name="From")
    late_interval = models.CharField(max_length=100,blank=True,null=True,verbose_name="To")
    max_ma = models.CharField(max_length=10,blank=True,null=True,verbose_name="From Ma")
    min_ma = models.CharField(max_length=10,blank=True,null=True,verbose_name="To Ma")
    latitude = models.CharField(max_length=20,blank=True,null=True,verbose_name="경도")
    longitude = models.CharField(max_length=20,blank=True,null=True,verbose_name="위도")
    country = models.CharField(max_length=10,blank=True,null=True,verbose_name="국가")
    state = models.CharField(max_length=100,blank=True,null=True,verbose_name="State")
    county = models.CharField(max_length=100,blank=True,null=True,verbose_name="County")
    formation = models.CharField(max_length=100,blank=True,null=True)
    remarks = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.species_name + "@" + self.state
    def process_genus_name(self):
        name_list = self.species_name.split(" ")
        if len(name_list) > 0:
            self.genus_name = name_list[0]
