from multiprocessing.spawn import prepare
from unittest import runner
from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner, PhyloAnalog
from phylomanager.utils import PhyloTreefile
from django.core.management.base import BaseCommand
import subprocess
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal
import matplotlib.pyplot as plt
from Bio import Phylo
import io
import platform, tempfile

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def quit_gracefully(self,arg1,arg2):
        print('quit')
        sys.exit()

    def handle(self, **options):
        print(options)

        my_os = platform.system()
        if my_os == 'Linux':
            signal.signal(signal.SIGINT, self.quit_gracefully)   
            signal.signal(signal.SIGTERM, self.quit_gracefully)     
            #signal.signal(signal.SIGBREAK, self.quit_gracefully)     

        prev_runner = PhyloRunner.objects.all().order_by("-created_datetime")[0]
        if prev_runner.runner_status in ['ST','WK','SL']:
            print("prev_runner:", prev_runner.runner_status)
            # see if such process is still running
            if os.path.exists("/proc/"+str(prev_runner.procid)):
                # if running, then just return and exit
                return
            else:
                # otherwise set prev_runner as finished and run myself
                prev_runner.runner_status = 'FN'
                prev_runner.save()

        self.runner = PhyloRunner()
        self.runner.procid = os.getpid()
        self.runner.runner_status = "ST" #Starting
        self.runner.save()
        self.do_loop()

    def do_loop(self):
        my_os = platform.system()

        while( True ):
            runs = self.get_candidate_runs()
            if len(runs) == 0:
                print("sleep")
                self.runner.runner_status = "SL" #Sleeping
                self.runner.save()
                time.sleep(5)
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
                local_now = timezone.localtime(now)
                if run.run_status == 'QD':
                    run.run_status = 'IP'
                    run.start_datetime = now
                    run.save()
                now_string = local_now.strftime("%Y%m%d_%H%M%S")
                print(now_string)
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
                        original_leg_directory = ""
                        
                        
                        temp_directory = None
                        temp_directory_name = ""
                        if package.package_name == 'MrBayes' and my_os == 'Linux':
                            ''' MrBayes doesn't run if datafile path is longer than 100chars. 
                                So we use tempdir and copy all files after the analysis '''

                            original_leg_directory = leg_directory
                            temp_directory = tempfile.TemporaryDirectory()
                            temp_directory_name = temp_directory.name
                            leg_directory = os.path.join( temp_directory_name, leg.get_dirname() )
                            if not os.path.isdir( leg_directory ):
                                os.makedirs( leg_directory )
                            print("original leg directory", original_leg_directory, os.path.isdir( original_leg_directory))
                            print("leg directory", leg_directory, os.path.isdir( leg_directory))
                        else:
                            if not os.path.isdir( leg_directory ):
                                os.makedirs( leg_directory )


                        # update leg status
                        print("leg status update")
                        leg.leg_status = 'IP'
                        leg.start_datetime = timezone.now()
                        leg.leg_directory = leg_directory
                        leg.save()

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

                        print("writing data file")
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
                            #print( run_argument_list )

                        elif package.package_name == 'TNT':
                            # copy TNT script file
                            run_file_name = os.path.join( settings.BASE_DIR, "scripts", "aquickie.run" )
                            shutil.copy( run_file_name, leg_directory )
                            my_os = platform.system()
                            if my_os == 'Linux':
                                separator = ","
                            else:
                                separator = ";"

                            #run argument setting
                            run_argument_list = [ package.run_path, "proc", data_file_location, separator, "aquickie", separator ]

                        elif package.package_name == 'MrBayes':
                            command_filename = self.create_mrbayes_command_file( data_filename, leg_directory, leg )
                            run_argument_list = [package.run_path, command_filename]
                        
                        print( "argument list", run_argument_list )

                        stdout_filename = os.path.join( leg_directory, "output.log" )
                        stdout_fd = open(stdout_filename, "w")
                        stderr_filename = os.path.join( leg_directory, "error.log" )
                        stderr_fd = open(stderr_filename, "w")
                        print( "redirect file descriptors open")

                        #print( run_argument_list )
                        p1 = subprocess.Popen( run_argument_list, cwd=leg_directory, stdout=subprocess.PIPE, stderr=stderr_fd)
                        print( "p1 subprocess run", p1)
                        #p2 = subprocess.run(['python', 'manage.py', 'phylomonitor', package.package_name],cwd=settings.BASE_DIR,stdin=p1.stdout, stdout = stdout_fd)
                        monitor_argument_list =['python', 'manage.py', 'phylomonitor', '--package_name', package.package_name, '--leg_id', str(leg.id) ]
                        print("monitor argument", monitor_argument_list)
                        p2 = subprocess.run(monitor_argument_list,cwd=settings.BASE_DIR,stdin=p1.stdout, stdout = stdout_fd, stderr=stderr_fd)
                        print("p2 subprocess run", p2)

                        

                        #print( run_argument_list )
                        #subprocess.run( run_argument_list, cwd=leg_directory, stdout=stdout_fd, stderr=stderr_fd)
                        #print( "Sleeping 30seconds" )

                        stdout_fd.close()
                        stderr_fd.close()
                        print("closed stdout, stderr")

                        # update leg status
                        leg.leg_status = 'FN'
                        leg.leg_completion_percentage = 100
                        leg.finish_datetime = timezone.now()
                        leg.save()

                        print("leg done")

                        log.log_status = 'FN'
                        log.save()

                        if original_leg_directory != "":
                            #print("after leg done, original leg directory", original_leg_directory, os.path.isdir( original_leg_directory))
                            #print("after leg done, leg directory", leg_directory, os.path.isdir( leg_directory))

                            shutil.copytree(leg_directory, original_leg_directory)
                            leg.leg_directory = original_leg_directory
                            leg.save()


                        '''Tree file Processing'''
                        if package.package_name == 'IQTree':
                            tree_filename = os.path.join( leg.leg_directory, filename + ".phy.treefile" )
                            tree = Phylo.read( tree_filename, "newick" )
                        elif leg.leg_package.package_name == 'TNT':
                            phylo_data = run.phylodata
                            phylo_data.post_read()
                            #phylodata.taxa_list
                            #phylodata.post_read()
                            #print(phylodata.taxa_list)
                            tree_filename = os.path.join( leg.leg_directory, "aquickie.tre" )
                            #tree = Phylo.read( tree_filename, "nexus" )
                            tf = PhyloTreefile()
                            tf.readtree(tree_filename,'Nexus')
                            #print(tf.block_hash)
                            tree = Phylo.read(io.StringIO(tf.tree_text_hash['tnt_1']), "newick")
                            for clade in tree.find_clades():
                                if clade.name:
                                    taxon_index = int(clade.name) - 1
                                    clade.name = phylo_data.taxa_list[taxon_index]
                                    #print(clade.name)
                                    #clade.name = tf.taxa_hash[clade.name]

                        elif leg.leg_package.package_name == 'MrBayes':
                            tree_filename = os.path.join( leg.leg_directory, filename + ".nex1.con.tre" )
                            tf = PhyloTreefile()
                            tf.readtree(tree_filename,'Nexus')
                            #print(tf.tree_text_hash)
                            #tree_text = tf.tree_text_hash['con_50_majrule']
                            #handle = 
                            tree = Phylo.read(io.StringIO(tf.tree_text_hash['con_50_majrule']), "newick")
                            for clade in tree.find_clades():
                                if clade.name and tf.taxa_hash[clade.name]:
                                    #print(clade.name)
                                    clade.name = tf.taxa_hash[clade.name]

                        fig = plt.figure(figsize=(10, 20), dpi=100)
                        axes = fig.add_subplot(1, 1, 1)
                        Phylo.draw(tree, axes=axes,do_show=False)
                        #plt.show()
                        #buffer = io.BytesIO()
                        #print(tree_filename)
                        tree_imagefile = os.path.join( leg.leg_directory, "concensus_tree.svg" )
                        plt.savefig(tree_imagefile, format='svg')

                        
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
   mcmc nruns={nruns} ngen={ngen} samplefreq={samplefreq} file={dfname}1 burnin={burnin} Savebrlens=No;
   sump burnin={burnin};
   sumt burnin={burnin} Showtreeprobs=No;
end;""".format( dfname=data_filename, nst=leg.mcmc_nst, nrates=leg.mcmc_nrates, nruns=leg.mcmc_nruns, ngen=leg.mcmc_ngen, samplefreq=leg.mcmc_samplefreq,burnin=leg.mcmc_burnin)
        #print(command_text)

        command_filepath = os.path.join(leg_directory,command_filename)
        f = open(command_filepath, "w")
        f.write(command_text)
        f.close()
        return command_filepath

    def __del__(self):
        print('Destructor called.')
        if self.runner:
            print('runner finished.')
            self.runner.runner_status = "FN"    
            self.runner.save()
