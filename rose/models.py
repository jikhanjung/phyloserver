import pandas as pd
from django.db import models
from django.conf import settings
import os

# Create your models here.
class RoseOccurrence(models.Model):
    locality = models.CharField(max_length=200,blank=True,null=True)
    age = models.CharField(max_length=200,blank=True,null=True)
    comment = models.CharField(max_length=200,blank=True,null=True)
    strike = models.CharField(max_length=200,blank=True,null=True)
    dip = models.CharField(max_length=200,blank=True,null=True)
    length = models.CharField(max_length=200,blank=True,null=True)
    distance = models.CharField(max_length=200,blank=True,null=True)
    region = models.CharField(max_length=200,blank=True,null=True)
    symbol = models.CharField(max_length=200,blank=True,null=True)
    color = models.CharField(max_length=200,blank=True,null=True)
    rocktype1 = models.CharField(max_length=200,blank=True,null=True)
    rocktype2 = models.CharField(max_length=200,blank=True,null=True)
    rosefile = models.ForeignKey('RoseFile',on_delete=models.SET_NULL,blank=True,null=True)

class RoseFile(models.Model):
    file = models.FileField(upload_to='rose/files/')
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

        for index, row in df.iterrows():
            #print("index:", index)
            if pd.notna(row['각도']):
                occ = RoseOccurrence()
                occ.locality = row['주소']
                occ.age = row['시대']
                # see if we can convert the angle to a float
                angle = row['각도']
                try:
                    angle = float(angle)
                    angle = 270 - angle
                    angle = angle % 180
                except:
                    angle = -999
                occ.strike = angle
                occ.length = row['길이']
                occ.distance = row['거리']
                occ.rocktype1 = row['지층']
                occ.rocktype2 = row['대표암상']
                occ.symbol = row['기호']
                occ.region = row['지역']
                occ.dip = ''
                occ.comment = ''
                occ.rosefile = self
                occ.save()
                #print("occ:", occ)
