from multiprocessing.spawn import prepare
from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner, PhyloAnalog
from django.core.management.base import BaseCommand
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal
import subprocess

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        #print(options)
        runs = self.get_candidate_runs()
        for run in runs:
            #print(run, run.get_run_status_display())
            leg_list = run.leg_set.filter(leg_status__exact='QD')
            now = timezone.now()
            now_string = now.strftime("%Y%m%d_%H%M%S")

            run.run_directory = os.path.join("phylo_run", run.get_run_by, run.get_dirname() + "_" + now_string)
            run_abspath = os.path.join( settings.MEDIA_ROOT, run.run_directory )
            #run_abspath = os.path.join( "D:/", run.run_directory )
            print("run_abspath:", run_abspath)
            for leg in leg_list:
                package = leg.leg_package
                #print( "  ",leg, leg.get_leg_status_display() )
                #print("gonna execute", package, package.get_package_type_display(), "at", package.run_path)
                if package.package_name in ['IQTree','TNT', 'MrBayes']:
                    # update leg status
                    # create run/leg directory
                    #print( settings.MEDIA_ROOT, str(run.datafile) )
                    data_filename = os.path.split( str(run.datafile) )[-1]
                    filename, fileext = os.path.splitext(data_filename.upper())

                    original_file_location = os.path.join( settings.MEDIA_ROOT, str(run.datafile) )
                    leg_directory = os.path.join( run_abspath, leg.get_dirname())
                    leg.leg_directory = leg_directory
                    if not os.path.isdir( leg_directory ):
                        os.makedirs( leg_directory )

                    phylo_data = run.phylodata
                    phylo_data.post_read()
                    print(phylo_data.dataset_name)

                    #shutil.copy( original_file_location, leg_directory )
                    if package.package_name == 'IQTree':
                        fileext = '.phy'
                        datamatrix_str = phylo_data.as_phylip_format()
                    elif package.package_name in ['TNT','MrBayes']:
                        fileext = '.nex'
                        datamatrix_str = phylo_data.as_nexus_format()

                    data_filename = filename + fileext
                    data_file_location = os.path.join( leg_directory, data_filename )
                    data_fd = open(data_file_location,mode='w')
                    data_fd.write(datamatrix_str)
                    data_fd.close()

                    if package.package_name == 'IQTree':
                        #run analysis - IQTree
                        #run argument setting
                        run_argument_list = [ package.run_path, "-s", data_file_location, "-nt", "AUTO"]
                        if run.datatype == 'MO':
                            run_argument_list.extend( ["-st", "MORPH"] )
                        if leg.ml_bootstrap_type == 'NB':
                            run_argument_list.extend( ["-b", str(leg.ml_bootstrap)] )
                        elif leg.ml_bootstrap_type == 'UF':
                            run_argument_list.extend( ["-bb", str(leg.ml_bootstrap)] )
                        print( run_argument_list )

                    elif package.package_name == 'TNT':
                        # copy TNT script file
                        run_file_name = os.path.join( settings.BASE_DIR, "scripts", "aquickie.run" )
                        shutil.copy( run_file_name, leg_directory )

                        #run argument setting
                        run_argument_list = [ package.run_path, "proc", data_filename, ";", "aquickie", ";" ]

                    elif package.package_name == 'MrBayes':
                        command_filename = self.create_mrbayes_command_file( data_filename, leg_directory, leg )
                        run_argument_list = [package.run_path, command_filename]
                        print( run_argument_list )

                    stdout_filename = os.path.join( leg_directory, "output.log" )
                    stdout_fd = open(stdout_filename, "w")
                    stderr_filename = os.path.join( leg_directory, "error.log" )
                    stderr_fd = open(stderr_filename, "w")

                    print( run_argument_list )
                    p1 = subprocess.Popen( run_argument_list, cwd=leg_directory, stdout=subprocess.PIPE, stderr=stderr_fd)
                    #p2 = subprocess.run(['python', 'manage.py', 'phylomonitor', package.package_name],cwd=settings.BASE_DIR,stdin=p1.stdout, stdout = stdout_fd)
                    monitor_argument_list =['python', 'manage.py', 'phylomonitor', '--package_name', package.package_name, '--leg_id', str(leg.id) ]
                    p2 = subprocess.run(monitor_argument_list,cwd=settings.BASE_DIR,stdin=p1.stdout, stdout = stdout_fd)

                    print("run result:", p1)
                    #print( "Sleeping 30seconds" )

                    stdout_fd.close()
                    stderr_fd.close()

                    # update leg status
                    leg.leg_status = 'FN'
                    leg.finish_datetime = timezone.now()
                    #exit()
                    #leg.save()

                    
                #print("\n")
            #print("\n\n")
            finished_count = 0
            for leg in leg_list:
                if leg.leg_status == 'FN':
                    finished_count += 1
            if finished_count == len( leg_list ):
                run.run_status = 'FN'
                now = timezone.now()
                run.finish_datetime = now
                #run.save()

    def get_candidate_runs(self):
        runs = PhyloRun.objects.filter(run_status__in=['QD','IP']).order_by('created_datetime')
        return runs
    def create_mrbayes_command_file( self, data_filename, leg_directory, leg ):
        command_filename = "run.nex"
        leg_directory
        command_text = """begin mrbayes;
   set autoclose=yes nowarn=yes;
   execute {dfname};
   lset nst={nst} rates={nrates};
   mcmc nruns={nruns} ngen={ngen} samplefreq={samplefreq} file={dfname}1;
end;""".format( dfname=data_filename, nst=leg.mcmc_nst, nrates=leg.mcmc_nrates, nruns=leg.mcmc_nruns, ngen=leg.mcmc_ngen, samplefreq=leg.mcmc_samplefreq)
        #print(command_text)

        command_filepath = os.path.join(leg_directory,command_filename)
        f = open(command_filepath, "w")
        f.write(command_text)
        f.close()
        return command_filepath
