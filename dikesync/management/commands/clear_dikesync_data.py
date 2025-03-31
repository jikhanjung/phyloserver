from django.core.management.base import BaseCommand
from dikesync.models import DikeRecord, SyncEvent
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes all dikesync related data (DikeRecords and SyncEvents)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        try:
            # Get counts before deletion
            dike_record_count = DikeRecord.objects.count()
            sync_event_count = SyncEvent.objects.count()

            if not options['force']:
                # Ask for confirmation
                confirm = input(
                    f'This will delete {dike_record_count} DikeRecords and {sync_event_count} SyncEvents. '
                    'Are you sure you want to continue? [y/N]: '
                )
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.WARNING('Operation cancelled.'))
                    return

            # Delete all records in a transaction
            with transaction.atomic():
                # Delete all DikeRecords
                DikeRecord.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {dike_record_count} DikeRecords')
                )

                # Delete all SyncEvents
                SyncEvent.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {sync_event_count} SyncEvents')
                )

            self.stdout.write(self.style.SUCCESS('All dikesync data has been cleared successfully.'))

        except Exception as e:
            logger.error(f"Error clearing dikesync data: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error clearing dikesync data: {str(e)}')
            ) 