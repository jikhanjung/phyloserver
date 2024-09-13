from django.db import models
from nkfcluster.models import ChronoUnit

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.safestring import mark_safe
import os
import pandas as pd

ENVIRONMENT_CHOICES = (
    ('01', 'lacustrine'),
    ('02', 'channel'),
    ('03', 'pond'),
    ('04', 'floodplain'),
    ('05', 'terrestrial'),
    ('06', 'fluvial-lacustrine'),
    ('07', 'bay'),
    ('08', 'fluvial'),
)

class FrOccurrence(models.Model):
    locality = models.CharField(max_length=200,blank=True,null=True)
    country = models.CharField(max_length=200,blank=True,null=True)
    clade = models.CharField(max_length=200,blank=True,null=True)
    family = models.CharField(max_length=200,blank=True,null=True)
    genus = models.CharField(max_length=200,blank=True,null=True)
    origin = models.CharField(max_length=200,blank=True,null=True)
    epoch = models.CharField(max_length=200,blank=True,null=True)
    epoch_code = models.ForeignKey(ChronoUnit,on_delete=models.DO_NOTHING,blank=True,null=True,related_name='epoch_code')
    age = models.CharField(max_length=200,blank=True,null=True)
    age_code = models.ForeignKey(ChronoUnit,on_delete=models.DO_NOTHING,blank=True,null=True,related_name='age_code')
    environment = models.CharField(max_length=200,blank=True,null=True)
    environment_code = models.CharField(max_length=10,blank=True,null=True,choices=ENVIRONMENT_CHOICES)
    continent = models.CharField(max_length=200,blank=True,null=True)
    period = models.CharField(max_length=200,blank=True,null=True)
    period_code = models.ForeignKey(ChronoUnit,on_delete=models.DO_NOTHING,blank=True,null=True,related_name='period_code')
    reference = models.CharField(max_length=200,blank=True,null=True)
    frfile = models.ForeignKey('FrFile',on_delete=models.SET_NULL,blank=True,null=True)

    def __str__(self):
        return self.genus
    
    def update_chronounit(self):
        cu = ChronoUnit.objects.all()
        if self.age != None and self.age != '' and self.age != '?':
            age_code = cu.filter(name__iexact=self.age)
            if age_code != None:
                self.age_code = age_code.first()
        if self.epoch != None and self.epoch != '' and self.epoch != '?':
            epoch_name = self.epoch
            # if epoch_name contains "Early" or "Late", replace it with "Lower" and "Upper"
            if "Early" in epoch_name:
                epoch_name = epoch_name.replace("Early","Lower")
            if "Late" in epoch_name:
                epoch_name = epoch_name.replace("Late","Upper")
            epoch_code = cu.filter(name__iexact=epoch_name)
            if epoch_code != None:
                self.epoch_code = epoch_code.first()
        if self.period != None and self.period != '' and self.period != '?':
            period_code = cu.filter(name__iexact=self.period)
            if period_code != None:
                self.period_code = period_code.first()


    

class FrFile(models.Model):
    file = models.FileField(upload_to='freshwaterfish/files/')
    name = models.CharField(max_length=200,blank=True,null=True)
    comment = models.CharField(max_length=200,blank=True,null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    
    def process_rows(self):
        sheet_name = 'Sheet1'
        filepath = os.path.join( settings.MEDIA_ROOT, str(self.file) )
        df = pd.read_excel (filepath,sheet_name)
        #print(df)
        # locality	country	clade	family	genus	origin	epoch	age	environment	continent	period
        column_list = ['locality', 'country', 'clade', 'family', 'genus', 'origin', 'epoch', 'age', 'environment', 'continent', 'period', 'reference']

        for index, row in df.iterrows():
            #print("index:", index)
            
            if pd.notna(row['genus']):
                occ = FrOccurrence()
                for col in column_list:
                    if col in df.columns and pd.notna(row[col]) and hasattr(occ, col):
                        setattr(occ, col, row[col])
                for choice in ENVIRONMENT_CHOICES:
                    val, disp = choice
                    if disp.lower() == str(row['environment']).lower():
                        occ.environment_code = val
                        break
                if str(row['environment']).lower() == 'channal'.lower():
                    occ.environment_code = '02'
                occ.update_chronounit()
                occ.frfile = self
                #if 'reference' in df.columns:
                #    occ.reference = row['reference']
                occ.save()
                #print("occ:", occ)
