from multiprocessing.spawn import prepare
from unittest import runner
from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner, PhyloAnalog
from django.core.management.base import BaseCommand
import subprocess
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def quit_gracefully(self,arg1,arg2):
        print('quit')
        sys.exit()

    def handle(self, **options):
        print(options)

        #signal.signal(signal.SIGINT, self.quit_gracefully)   
        #signal.signal(signal.SIGTERM, self.quit_gracefully)     
        #signal.signal(signal.SIGBREAK, self.quit_gracefully)     

        self.runner = PhyloRunner()
        self.runner.procid = os.getpid()
        self.runner.runner_status = "ST" #Starting
        self.runner.save()
        self.do_loop()

    def do_loop(self):
        while( True ):
            runs = self.get_candidate_runs()
            if len(runs) == 0:
                print("sleep")
                self.runner.runner_status = "SL" #Sleeping
                self.runner.save()
                time.sleep(20)
                #print("wake up!")
            else:
                print("working with", len(runs), "run(s)")
                self.runner.runner_status = "WK" #Working
                self.runner.save()

            for run in runs:
                print(run, run.get_run_status_display() )
                leg_list1 = run.leg_set.all()
                leg_list2 = run.leg_set.filter(leg_status__exact='QD')
                leg_list3 = PhyloLeg.objects.filter(run_id__exact=run.id,leg_status__exact='QD')
                leg_list4 = PhyloLeg.objects.filter(run_id__exact=run.id)
                leg_list = leg_list2
                print(run, run.id, run.get_run_status_display(), leg_list1, leg_list2, leg_list3, leg_list4 )
                now = timezone.now()
                if run.run_status == 'QD':
                    run.run_status = 'IP'
                    run.start_datetime = now
                    run.save()
                now_string = now.strftime("%Y%m%d_%H%M%S")
                #run_directory = 
                run.run_directory = os.path.join( "phylo_run", run.get_run_by, run.get_dirname() + "_" + now_string )
                print( "run directory:", run.run_directory )
                run.save()
                run_abspath = os.path.join( settings.MEDIA_ROOT, run.run_directory )
                for leg in leg_list:
                    package = leg.leg_package
                    #print( "  ",leg, leg.get_leg_status_display() )
                    print("gonna execute", package, package.get_package_type_display(), "at", package.run_path)
                    if package.package_name in ['IQTree','TNT', 'MrBayes']:
                        # update leg status
                        leg.leg_status = 'IP'
                        leg.start_datetime = timezone.now()
                        leg.save()

                        log = PhyloAnalog()
                        log.leg = leg
                        log.runner = self.runner
                        log.log_status = 'IP'
                        log.save()

                        # create run/leg directory
                        #print( settings.MEDIA_ROOT, str(run.datafile) )
                        data_filename = os.path.split( str(run.datafile) )[-1]
                        filename, fileext = os.path.splitext(data_filename.upper())

                        original_file_location = os.path.join( settings.MEDIA_ROOT, str(run.datafile) )
                        leg_directory = os.path.join( run_abspath, leg.get_dirname())
                        if not os.path.isdir( leg_directory ):
                            os.makedirs( leg_directory )
                        
                        phylo_data = run.phylodata
                        phylo_data.post_read()
                        # copy data file
                        #print( original_file_location, run_directory, leg_directory )

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


                        #shutil.copy( original_file_location, leg_directory )
                        #target_file_location = os.path.join( leg_directory, data_filename )

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
                            run_argument_list = [ package.run_path, "proc", data_file_location, ";", "aquickie", ";" ]

                        elif package.package_name == 'MrBayes':
                            command_filename = self.create_mrbayes_command_file( data_filename, leg_directory, leg )
                            run_argument_list = [package.run_path, command_filename]
                            print( run_argument_list )

                        stdout_filename = os.path.join( leg_directory, "output.log" )
                        stdout_fd = open(stdout_filename, "w")
                        stderr_filename = os.path.join( leg_directory, "error.log" )
                        stderr_fd = open(stderr_filename, "w")

                        #print( run_argument_list )
                        subprocess.run( run_argument_list, cwd=leg_directory, stdout=stdout_fd, stderr=stderr_fd)
                        #print( "Sleeping 30seconds" )

                        stdout_fd.close()
                        stderr_fd.close()

                        # update leg status
                        leg.leg_status = 'FN'
                        leg.finish_datetime = timezone.now()
                        leg.save()

                        log.log_status = 'FN'
                        log.save()
                        
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
                    run.save()

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

    def __del__(self):
        print('Destructor called, runner deleted.')
        self.runner.runner_status = "FN"    
        self.runner.save()
