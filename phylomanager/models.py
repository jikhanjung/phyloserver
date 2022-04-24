from django.db import models

class PhyloPackage(models.Model):
    PACKAGE_TYPE_CHOICES = [
        ('BY', 'Bayesian'),
        ('MP', 'Maximum Parsimony'),
        ('ML', 'Maximum Likelihood'),
    ]
    package_name = models.CharField(max_length=200,blank=True,null=True)
    package_version = models.CharField(max_length=200,blank=True,null=True)
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES,blank=True,null=True )
    run_path = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.package_name

class PhyloRun(models.Model):
    RUN_STATUS_CHOICES = [
        ('QD','Queued'),
        ('IP','In progress'),
        ('FN','Finished'),
        ('ER','Error occurred'),
    ]
    start_datetime = models.DateTimeField(blank=True,null=True)
    finish_datetime = models.DateTimeField(blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    run_title = models.CharField(max_length=200,blank=True,null=True)
    run_status = models.CharField(max_length=10,choices=RUN_STATUS_CHOICES,default='QD',blank=True,null=True)
    run_by = models.CharField(max_length=200,blank=True,null=True)
    datafile = models.FileField(upload_to='phylorun_datafile',blank=True)
    run_directory = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.run_title

class PhyloModel(models.Model):
    model_name = models.CharField(max_length=200,blank=True,null=True)
    model_type = models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.model_name

class PhyloLeg(models.Model):
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
    PACKAGE_TYPE_CHOICES = [
        ('BY', 'Bayesian'),
        ('MP', 'Maximum Parsimony'),
        ('ML', 'Maximum Likelihood'),
    ]
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
    ml_bootstrap = models.IntegerField(default=0,blank=True,null=True)
    ml_bootstrap_type = models.CharField(max_length=10,choices=BOOTSTRAP_TYPE_CHOICES,blank=True,null=True)
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
