from phylomanager.models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Customized load data for DB migration"

    def handle(self, **options):
        runs = self.get_candidate_runs()
        for run in runs:
            print( run, run.get_run_status_display() )
            for leg in run.leg_set.all():
                print( "  ",leg, leg.get_leg_status_display() )

    def get_candidate_runs(self):
        runs = PhyloRun.objects.filter(run_status__in=['QD','IP']).order_by('created_datetime')
        return runs

