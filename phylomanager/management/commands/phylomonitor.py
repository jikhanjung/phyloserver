import sys
import re, os, json

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

    def add_arguments(self, parser):
        parser.add_argument('--package_name')
        parser.add_argument('--leg_id')

    def handle(self, **options):
        print(options)
        package_name = options['package_name']
        leg_id = int(options['leg_id'])
        leg = PhyloLeg.objects.get(id=leg_id)
        print("package_name:", leg.leg_package.package_name)
        leg_directory = leg.leg_directory
        progress_filename = os.path.join( leg_directory, "progress.log" )
        progress_filename_fd = open(progress_filename, "w",buffering=1)

        total_step = 0
        curr_step = 0
        if package_name in ['IQTree']:
            total_step = leg.ml_bootstrap
        elif package_name in ['MrBayes']:
            total_step = leg.mcmc_ngen

        for line in sys.stdin:
            progress_found = False
            if package_name in ['IQTree']:
                progress_match = re.match("===> START BOOTSTRAP REPLICATE NUMBER (\d+)",line)

                if progress_match:
                    progress_found = True
                    curr_step = progress_match.group(1)
                    print("progress detected", curr_step, flush=True)
                    #print("<", line,">", flush=True,end='')

            elif package_name in ['MrBayes']:
                progress_match = re.match("^\s+(\d+).*(\d+:\d+:\d+)$",line)
                #progress_match = re.match("(\d+)\s+-- .+ --\s+(\d+:\d+\d+)",line)
                if progress_match:
                    progress_found = True
                    curr_step = progress_match.group(1)
                    print("progress detected", curr_step, flush=True)
                    
            if progress_found:
                percentage = float(int( ( float(curr_step) / float(total_step) ) * 10000 )) / 100.0
                leg.leg_completion_percentage = percentage
                leg.save()
                progress_filename_fd.write(line)
            print(line,flush=True,end='')
        progress_filename_fd.close()


