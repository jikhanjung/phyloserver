import sys

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
        parser.add_argument('package_name', nargs='+', type=str)

    def handle(self, **options):
        print(options)
        for line in sys.stdin:
            if line.find('START BOOTSTRAP REPLICATE NUMBER') > -1:
                print("<", line,">", flush=True,end='')
            print("[",line,"]", flush=True,end='')

