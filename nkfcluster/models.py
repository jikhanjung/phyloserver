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
    ("SH","승호"),
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
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES,blank=True,null=True )
    def __str__(self):
        return self.species_name + " @" + self.location
