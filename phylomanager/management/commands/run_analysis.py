from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg
from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        runs = self.get_candidate_runs()
        for run in runs:
            print( run, run.get_run_status_display() )
            for leg in run.leg_set.all():
                package = leg.leg_package;
                print( "  ",leg, leg.get_leg_status_display() )
                print("gonna execute", package, package.get_package_type_display(), "at", package.run_path)
                if package.package_name == 'IQTree':
                    # create run directory, copy file, run IQTree
                    
                    subprocess.run([ package.run_path, "-i", run.)

    def get_candidate_runs(self):
        runs = PhyloRun.objects.filter(run_status__in=['QD','IP']).order_by('created_datetime')
        return runs
