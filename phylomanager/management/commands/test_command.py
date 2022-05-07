from multiprocessing.spawn import prepare
from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner, PhyloAnalog
from django.core.management.base import BaseCommand
from django.conf import settings
import os, shutil, sys
import time, datetime
from django.utils import timezone
import signal
import subprocess

from backports import zoneinfo

class Command(BaseCommand):
    help = "Customized load data for DB migration"
    runner = None

    def handle(self, **options):
        now = timezone.now()
        local_now = timezone.localtime(now)
        print(now)
        print(local_now)
        #now_string = now.strftime("%Y%m%d_%H%M%S")
        #timezone.activate(zoneinfo.ZoneInfo(settings.TIME_ZONE))
        #current_tz = timezone.get_current_timezone()


##>>> from django.utils import timezone
#>>> timezone.activate(zoneinfo.ZoneInfo("Asia/Singapore"))
# For this example, we set the time zone to Singapore, but here's how
# you would obtain the current time zone in the general case.
#>>> current_tz = timezone.get_current_timezone()