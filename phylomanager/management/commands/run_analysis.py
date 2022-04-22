from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg
from django.core.management.base import BaseCommand
import subprocess
from django.conf import settings
import os, shutil
import time, datetime

class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        runs = self.get_candidate_runs()
        for run in runs:
            #print(run, run.get_run_status_display())
            leg_list = run.leg_set.filter(leg_status__exact='QD')
            now = datetime.datetime.now()
            if run.run_status == 'QD':
                run.run_status = 'IP'
                run.start_datetime = now
                run.save()
            now_string = now.strftime("%Y%m%d_%H%M%S")
            run_directory = os.path.join( settings.MEDIA_ROOT, "phylo_run", "run_"+str(run.id) + "_" + now_string )
            for leg in leg_list:
                package = leg.leg_package
                #print( "  ",leg, leg.get_leg_status_display() )
                #print("gonna execute", package, package.get_package_type_display(), "at", package.run_path)
                if package.package_name in ['IQTree','TNT']:
                    # update leg status
                    leg.leg_status = 'IP'
                    leg.start_datetime = now
                    leg.save()

                    # create run/leg directory
                    #print( settings.MEDIA_ROOT, str(run.datafile) )
                    filename = os.path.split( str(run.datafile) )[-1]
                    original_file_location = os.path.join( settings.MEDIA_ROOT, str(run.datafile) )
                    leg_directory = os.path.join( run_directory, "leg_"+str(leg.id) + "/")
                    if not os.path.isdir( leg_directory ):
                        os.makedirs( leg_directory )
                    
                    # copy data file
                    #print( original_file_location, run_directory, leg_directory )
                    shutil.copy( original_file_location, leg_directory )
                    target_file_location = os.path.join( leg_directory, filename )

                    # run analysis - IQTree
                    if package.package_name =='IQTree':
                        #run argument setting
                        run_argument_list = [ package.run_path, "-s", target_file_location, "-nt", "AUTO", "-st", "MORPH" ]

                    elif package.package_name =='TNT':
                        # copy TNT script file
                        run_file_name = os.path.join( settings.BASE_DIR, "scripts", "aquickie.run" )
                        shutil.copy( run_file_name, leg_directory )

                        #run argument setting
                        run_argument_list = [ package.run_path, "proc", target_file_location, ";", "aquickie", ";" ]

                    #print( run_argument_list )
                    subprocess.run( run_argument_list, cwd=leg_directory)
                    #print( "Sleeping 30seconds" )
                    #time.sleep(30)

                    # update leg status
                    leg.leg_status = 'FN'
                    now = datetime.datetime.now()
                    leg.finish_datetime = now
                    leg.save()
                    
                #print("\n")
            #print("\n\n")
            finished_count = 0
            for leg in leg_list:
                if leg.leg_status == 'FN':
                    finished_count += 1
            if finished_count == len( leg_list ):
                run.run_status = 'FN'
                now = datetime.datetime.now()
                run.finish_datetime = now
                run.save()

    def get_candidate_runs(self):
        runs = PhyloRun.objects.filter(run_status__in=['QD','IP']).order_by('created_datetime')
        return runs
