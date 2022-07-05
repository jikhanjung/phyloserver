from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from .utils import PhyloDatafile
import json
from django.utils.safestring import mark_safe
from Bio import Phylo

RUN_STATUS_CHOICES = [
    ('DU','Data uploaded'),
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
    # dataset properties
    dataset_name = models.CharField(max_length=200,blank=True,null=True)
    datatype = models.CharField(max_length=10,blank=True,null=True,choices=DATATYPE_CHOICES,default='MO')
    # actual data related
    n_taxa = models.IntegerField(blank=True,null=True)
    n_chars = models.IntegerField(blank=True,null=True)
    taxa_list_json = models.TextField(blank=True,null=True)
    character_definition_hash_json = models.TextField(blank=True,null=True)
    matrix_settings_json = models.TextField(blank=True,null=True) # default: gap=- missing=?
    # datamatrix
    datamatrix_json = models.TextField(blank=True,null=True)

    # analysis related
    mrbayes_block = models.TextField(blank=True,null=True)
    nexus_command_hash_json = models.TextField(blank=True,null=True)
    # original text from text file such as .phy, .nex, .tnt
    file_wholetext = models.TextField(blank=True,null=True)
    file_type = models.CharField(max_length=20,blank=True,null=True)

    taxa_list = []
    datamatrix = []
    character_definition_hash = {}
    matrix_settings_hash = {}
    nexus_command_hash = {}
    DEFAULTS = { 'gap': '-', 'missing': '?', 'datatype': 'standard' }

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
            #print("formatted_data_list:", formatted_data_list)
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

    def post_read(self):
        if self.taxa_list_json and self.taxa_list_json != '':
            self.taxa_list = json.loads(self.taxa_list_json)
        if self.character_definition_hash_json and self.character_definition_hash_json != '':
            self.character_definition_hash = json.loads(self.character_definition_hash_json)
        if self.datamatrix_json and self.datamatrix_json != '':
            self.formatted_data_list = json.loads(self.datamatrix_json)
        if self.nexus_command_hash_json and self.nexus_command_hash_json != '':
            self.nexus_command_hash = json.loads(self.nexus_command_hash_json)
        print(self.nexus_command_hash)

    def pre_save(self):
        if len(self.taxa_list) > 0:
            self.taxa_list_json = json.dumps(self.taxa_list,indent=4)
        if len(self.character_definition_hash) > 0:
            self.character_definition_hash_json = json.dumps(self.character_definition_hash,indent=4)
        if len(self.formatted_data_list) > 0:
            self.datamatrix_json = json.dumps(self.formatted_data_list,indent=4)
        if self.nexus_command_hash:
            self.nexus_command_hash_json = json.dumps(self.nexus_command_hash,indent=4)
        if self.block_hash and 'MRBAYES' in self.block_hash.keys():
            self.mrbayes_block = self.block_hash['MRBAYES']

    def loadfile(self,filepath):
        datafile_obj = PhyloDatafile()        
        original_file_location = os.path.join( settings.MEDIA_ROOT, str(filepath) )
        ret = datafile_obj.loadfile(original_file_location)
        #print("readfile return value:", ret)
        #print(self.phylo_datafile)
        if ret:
            self.dataset_name = datafile_obj.dataset_name
            self.file_wholetext = datafile_obj.file_text

            self.n_taxa = datafile_obj.n_taxa
            self.n_chars = datafile_obj.n_chars
            self.taxa_list = datafile_obj.taxa_list
            self.character_definition_hash = datafile_obj.character_definition_hash
            self.formatted_data_list = datafile_obj.formatted_data_list
            self.formatted_data_hash = datafile_obj.formatted_data_hash
            self.block_hash = datafile_obj.block_hash
            self.nexus_command_hash = datafile_obj.nexus_command_hash

            #print("post load",self.formatted_data_list)
            
            #if datafile_obj.file_type == 'Nexus':
            #    if datafile_obj.block_hash['MRBAYES']:
            #        self.mrbayes_block = datafile_obj.block_as_json('MRBAYES')
            #    if datafile_obj.command_hash:
            #        self.nexus_command_json = datafile_obj.command_hash_as_json()
        else:
            return False

        return True

    # when exporting as file
    def matrix_as_string(self,parens=["(",")"],separator=" "):
        matrix_string = ""
        #print("separator=["+separator+"]")
        for idx, taxon in enumerate(self.taxa_list):
            #print("taxon:",taxon)
            taxon_string = taxon + " "
            #matrix_string += taxon + " "
            formatted_data = self.formatted_data_list[idx].copy()
            taxon_name = formatted_data.pop(0)
            #print(formatted_data)
            for char_state in formatted_data:
                #print("char:",char_state)
                if type(char_state) is list:
                    taxon_string += parens[0] + separator.join(char_state) + parens[1]
                    #print("poly:",parens[0] + separator.join(char_state) + parens[1])
                else:
                    taxon_string += char_state
            matrix_string += taxon_string + "\n"
        return matrix_string

    # to save in database
    def matrix_as_json(self):
        return json.dumps(self.formatted_data_list,indent=4)

    def as_phylip_format(self):
        phylip_string = ""
        data_string = self.matrix_as_string()
        phylip_string += str(self.n_taxa) + " " + str(self.n_chars) + "\n"
        phylip_string += data_string
        return phylip_string

    def as_tnt_format(self):
        tnt_string = ""
        data_string = self.matrix_as_string()
        tnt_string += "xread '" + self.dataset_name + "' " + str(self.phylo_matrix.n_chars) + " " + str(self.phylo_matrix.n_taxa) + "\n"
        tnt_string += data_string
        tnt_string += ";\n"
        return tnt_string

    def as_nexus_format(self):
        nexus_string = ""
        data_string = self.matrix_as_string()
        command_string = self.command_as_string()
        nexus_string += "#NEXUS\n\n"
        nexus_string += "begin data;\n"
        nexus_string += command_string
        nexus_string += "matrix\n"
        nexus_string += data_string
        nexus_string += ";\n"
        nexus_string += "end;\n"
        return nexus_string
    
    def block_as_json(self,block_name):
        if self.block_hash[block_name]:
            return json.dumps(self.block_hash[block_name],indent=4)

    def command_hash_as_json(self):
        return json.dumps(self.command_hash)

    def command_as_string(self):
        command_string = ""
        if self.nexus_command_hash:
                
            for key1 in self.nexus_command_hash.keys():
                variable_list = []
                for key2 in self.nexus_command_hash[key1].keys():
                    variable_list.append( key2 + "=" + self.nexus_command_hash[key1][key2] )
                command_string += key1 + " " + " ".join(variable_list) + ";\n"
            #print(command_string)
        else:
            command_string += "dimensions ntax={ntax} nchar={nchar};\n".format(ntax=self.n_taxa, nchar=self.n_chars)
            command_string += "format datatype={datatype} gap={gap} missing={missing};\n".format(datatype=self.DEFAULTS['datatype'], gap=self.DEFAULTS['gap'], missing=self.DEFAULTS['missing'])
        return command_string


class PhyloRun(models.Model):

    start_datetime = models.DateTimeField(blank=True,null=True)
    finish_datetime = models.DateTimeField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    run_title = models.CharField(max_length=200,blank=True,null=True)
    run_status = models.CharField(max_length=10,choices=RUN_STATUS_CHOICES,default='DU',blank=True,null=True)
    run_by = models.CharField(max_length=200,blank=True,null=True)
    run_by_user = models.ForeignKey(PhyloUser,blank=True,null=True,on_delete=models.CASCADE)
    datafile = models.FileField(upload_to='phylorun_datafile',blank=True)
    datatype = models.CharField(max_length=10,blank=True,null=True,choices=DATATYPE_CHOICES,default='MO')
    phylodata = models.ForeignKey(PhyloData,on_delete=models.CASCADE,blank=True,null=True)
    run_directory = models.CharField(max_length=200,blank=True,null=True)

    def process_datafile(self):
        if self.datafile and self.datafile != '':
            print(self.datafile)
            self.phylodata = PhyloData()
            self.phylodata.loadfile(self.datafile)
        return

    @property
    def get_run_by(self):
        if self.run_by_user is not None:
            return self.run_by_user.username
        elif self.run_by is not None:
            return self.run_by
        else:
            return "Nobody"


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
    leg_directory = models.CharField(max_length=200,blank=True,null=True)
    leg_completion_percentage = models.FloatField(blank=True,null=True)
    leg_completion_estimation = models.DateTimeField(blank=True,null=True)
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

    def has_tree(self):
        run = self.run
        data_filename = os.path.split( str(run.datafile) )[-1]
        filename, fileext = os.path.splitext(data_filename.upper())
        if self.leg_package.package_name == 'IQTree':
            tree_filename = os.path.join( self.leg_directory, filename + ".phy.treefile" )
        elif self.leg_package.package_name == 'MrBayes':
            tree_filename = os.path.join( self.leg_directory, filename + ".nex1.con.tre" )
        elif self.leg_package.package_name == 'TNT':
            tree_filename = os.path.join( self.leg_directory, "aquickie.tre" )
        
    @property
    def get_tree(self):
        run = self.run
        if self.leg_package.package_name == 'IQTree':
            data_filename = os.path.split( str(run.datafile) )[-1]
            filename, fileext = os.path.splitext(data_filename.upper())

            tree_filename = os.path.join( self.leg_directory, filename + ".phy.treefile" )
            if os.path.exists( tree_filename ):
                tree = Phylo.read( tree_filename, "newick" )
                return Phylo.draw_ascii(tree)
            else:
                return tree_filename

class PhyloRunner(models.Model):
    procid = models.CharField(max_length=20,blank=True,null=True)
    runner_status = models.CharField(max_length=20,choices=RUNNER_STATUS_CHOICES,blank=True,null=True)
    command = models.CharField(max_length=20,blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

class PhyloAnalog(models.Model):
    runner = models.ForeignKey(PhyloRunner,on_delete=models.CASCADE,related_name='log_set')
    run = models.ForeignKey(PhyloRun,on_delete=models.CASCADE,related_name='log_set',null=True)
    leg = models.ForeignKey(PhyloLeg,on_delete=models.CASCADE,related_name='log_set',null=True)
    log_status = models.CharField(max_length=20,choices=LOG_STATUS_CHOICES,blank=True,null=True)
    log_text = models.TextField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

