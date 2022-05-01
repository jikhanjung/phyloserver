from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from .utils import PhyloDatafile
import json
from django.utils.safestring import mark_safe

RUN_STATUS_CHOICES = [
    ('QD','Queued'),
    ('IP','In progress'),
    ('FN','Finished'),
    ('ER','Error occurred'),
]

DATATYPE_CHOICES = [
    ('MO','Morphology'),
    ('DN','DNA'),
    ('RN','RNA'),
    ('AA','Amino acid'),
]

PACKAGE_TYPE_CHOICES = [
    ('BY', 'Bayesian'),
    ('MP', 'Maximum Parsimony'),
    ('ML', 'Maximum Likelihood'),
]

LEG_STATUS_CHOICES = [
    ('QD','Queued'),
    ('IP','In progress'),
    ('FN','Finished'),
    ('ER','Error occurred'),
]

BOOTSTRAP_TYPE_CHOICES = [ 
    ('NB','Normal Bootstrap'),
    ('UF','Ultra Fast Bootstrap(IQTree)'),
]

RUNNER_STATUS_CHOICES = [
    ('ST','Starting'),
    ('SL','Sleeping'),
    ('WK','Working'),
    ('FN','Finished'),
]

LOG_STATUS_CHOICES = [
    ('IP','In progress'),
    ('FN','Finished'),
    ('ER','Error occurred'),
]

class PhyloPackage(models.Model):
    package_name = models.CharField(max_length=200,blank=True,null=True)
    package_version = models.CharField(max_length=200,blank=True,null=True)
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES,blank=True,null=True )
    run_path = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.package_name

class PhyloUser(AbstractUser):
    firstname = models.CharField( max_length=50, blank=True, null=True,verbose_name=u'이름')
    lastname = models.CharField( max_length=50, blank=True, null=True,verbose_name=u'성')
    
    @property
    def korean_fullname(self):
        return self.lastname + self.firstname

    def __str__(self):
        return self.username

class PhyloData(models.Model):

    dataset_name = models.CharField(max_length=200,blank=True,null=True)
    datatype = models.CharField(max_length=10,blank=True,null=True,choices=DATATYPE_CHOICES,default='MO')
    n_taxa = models.IntegerField(blank=True,null=True)
    n_chars = models.IntegerField(blank=True,null=True)
    taxa_list = models.TextField(blank=True,null=True)
    char_list = models.TextField(blank=True,null=True)
    datamatrix_json = models.TextField(blank=True,null=True)
    filetext = models.TextField(blank=True,null=True)

    @property
    def datamatrix_as_list(self):
        if self.datamatrix_json:
            formatted_data_list = json.loads(self.datamatrix_json)
            return formatted_data_list
        else:
            return ""

    @property
    def datamatrix_as_table_rows(self):
        if self.datamatrix_json:
            formatted_data_list = json.loads(self.datamatrix_json)
            table_row_str = "<tr><th></th>"
            for col_idx in range(len(formatted_data_list[0])-1):
                table_row_str += "<th><div class='char_header'>" + str(col_idx+1) + "</div></th>"
            table_row_str += "</tr>\n"
            for taxon_chars in formatted_data_list:
                taxon_name = taxon_chars.pop(0)
                table_row_str += "<tr><th>" + taxon_name + "</th>"
                char_list_str = ""
                for chars in taxon_chars:
                    if type(chars) == list:
                        char_list_str += "<td><div class='char_state'>" + " ".join(chars) + "</div></td>"
                    else:
                        char_list_str += "<td><div class='char_state'>" + chars + "</div></td>"
                #table_row_st
                table_row_str += char_list_str + "</tr>\n"
            #print(table_row_str)
            return mark_safe(table_row_str)
        else:
            return ""


    def loadfile(self,filepath):
        self.phylo_datafile = PhyloDatafile()        
        original_file_location = os.path.join( settings.MEDIA_ROOT, str(filepath) )
        ret = self.phylo_datafile.readfile(original_file_location)
        #print("readfile return value:", ret)
        #print(self.phylo_datafile)
        if ret:
            datafile = self.phylo_datafile
            self.dataset_name = datafile.dataset_name
            self.n_taxa = datafile.phylo_matrix.n_taxa
            self.n_chars = datafile.phylo_matrix.n_chars
            self.taxa_list = datafile.phylo_matrix.taxa_list_as_string()
            self.char_list = datafile.phylo_matrix.char_list_as_string()
            self.datamatrix_json = datafile.phylo_matrix.matrix_as_json()
            self.filetext = datafile.file_text       
        else:
            return False

        return True

class PhyloRun(models.Model):

    start_datetime = models.DateTimeField(blank=True,null=True)
    finish_datetime = models.DateTimeField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    run_title = models.CharField(max_length=200,blank=True,null=True)
    run_status = models.CharField(max_length=10,choices=RUN_STATUS_CHOICES,default='QD',blank=True,null=True)
    run_by = models.CharField(max_length=200,blank=True,null=True)
    run_by_user = models.ForeignKey(PhyloUser,blank=True,null=True,on_delete=models.SET_NULL)
    datafile = models.FileField(upload_to='phylorun_datafile',blank=True)
    datatype = models.CharField(max_length=10,blank=True,null=True,choices=DATATYPE_CHOICES,default='MO')
    phylodata = models.ForeignKey(PhyloData,on_delete=models.DO_NOTHING,blank=True,null=True)
    run_directory = models.CharField(max_length=200,blank=True,null=True)

    def process_datafile(self):
        if self.datafile and self.datafile != '':
            print(self.datafile)
            self.phylodata = PhyloData()
            self.phylodata.loadfile(self.datafile)
        return

    @property
    def get_run_by(self):
        if self.run_by_user is None:
            return self.run_by
        else:
            return self.run_by_user.username

    @property
    def get_number_of_legs(self):
        return len(self.leg_set.all())
        

    def __str__(self):
        return self.run_title

    def get_dirname(self):
        if self.run_title:
            return self.run_title.replace(" ","_")
        else:
            return "run_" + str(self.id)


class PhyloModel(models.Model):
    model_name = models.CharField(max_length=200,blank=True,null=True)
    model_type = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.model_name

class PhyloLeg(models.Model):
    run = models.ForeignKey(PhyloRun, on_delete=models.CASCADE,related_name='leg_set')
    leg_sequence = models.IntegerField(blank=True,null=True)
    leg_title = models.CharField(max_length=200,blank=True,null=True)
    leg_status = models.CharField(max_length=10,choices=LEG_STATUS_CHOICES,default='QD',blank=True,null=True)
    leg_result = models.CharField(max_length=200,blank=True,null=True)
    leg_package = models.ForeignKey(PhyloPackage, on_delete=models.CASCADE)
    leg_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES,default='MP',blank=True,null=True)
    start_datetime = models.DateTimeField(blank=True,null=True)
    finish_datetime = models.DateTimeField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    ml_bootstrap = models.IntegerField(default=1000,blank=True,null=True)
    ml_bootstrap_type = models.CharField(max_length=10,choices=BOOTSTRAP_TYPE_CHOICES,default='NB',blank=True,null=True)
    substitution_model = models.CharField(max_length=100,blank=True,null=True)
    mcmc_burnin = models.IntegerField(blank=True,null=True,default=1000)
    mcmc_relburnin = models.BooleanField(default=False)
    mcmc_burninfrac = models.FloatField(blank=True,null=True)
    mcmc_ngen = models.IntegerField(blank=True,null=True,default=10000)
    mcmc_nst = models.IntegerField(blank=True,null=True,default=6)
    mcmc_nrates = models.CharField(max_length=50,blank=True,null=True,default='gamma')
    mcmc_printfreq = models.IntegerField(blank=True,null=True)
    mcmc_samplefreq = models.IntegerField(blank=True,null=True,default=100)
    mcmc_nruns = models.IntegerField(blank=True,null=True,default=1)
    mcmc_nchains = models.IntegerField(blank=True,null=True,default=1)
    def __str__(self):
        return self.leg_title

    def get_dirname(self):
        if self.leg_title:
            return self.leg_title.replace(" ","_")
        else:
            return "leg_" + str(self.id)

class PhyloRunner(models.Model):
    procid = models.CharField(max_length=20,blank=True,null=True)
    runner_status = models.CharField(max_length=20,choices=RUNNER_STATUS_CHOICES,blank=True,null=True)
    command = models.CharField(max_length=20,blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

class PhyloAnalog(models.Model):
    runner = models.ForeignKey(PhyloRunner,on_delete=models.CASCADE,related_name='log_set')
    leg = models.ForeignKey(PhyloLeg,on_delete=models.DO_NOTHING,related_name='log_set')
    log_status = models.CharField(max_length=20,choices=LOG_STATUS_CHOICES,blank=True,null=True)
    log_text = models.TextField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

