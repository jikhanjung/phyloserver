from django.core.management.base import BaseCommand
from django.db.models import Count
from dikesync.models import DikeRecord
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clears duplicate DikeRecord entries based on lat_1, lng_1, angle, and distance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def format_record_info(self, record):
        """Helper function to format record information consistently"""
        return (
            f'  - ID: {record.id}, '
            f'Location: ({record.lat_1}, {record.lng_1}), '
            f'Angle: {record.angle}, '
            f'Distance: {record.distance}, '
            f'Modified: {record.modified_date}, '
            f'Unique ID: {record.unique_id}'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find duplicates based on the specified fields
        duplicates = DikeRecord.objects.values(
            'lat_1', 'lng_1', 'angle', 'distance'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate records found.'))
            return

        total_duplicates = 0
        records_to_delete = []

        with transaction.atomic():
            for dup in duplicates:
                # Get all records with these values, ordered by modified_date descending
                # to keep the most recent record
                records = DikeRecord.objects.filter(
                    lat_1=dup['lat_1'],
                    lng_1=dup['lng_1'],
                    angle=dup['angle'],
                    distance=dup['distance']
                ).order_by('-modified_date')  # Note the minus sign to sort in descending order

                # Get the IDs of records to keep and delete
                keep_record = records.first()  # This will now be the most recent record
                delete_ids = list(records.exclude(id=keep_record.id).values_list('id', flat=True))
                
                if delete_ids:
                    delete_records = records.filter(id__in=delete_ids)
                    records_to_delete.extend(delete_records)
                    total_duplicates += len(delete_ids)

                    if dry_run:
                        self.stdout.write(self.style.WARNING(
                            f'\nDuplicate group found at location ({dup["lat_1"]}, {dup["lng_1"]}):'
                        ))
                        self.stdout.write(self.style.SUCCESS('Record to keep (most recent):'))
                        self.stdout.write(self.format_record_info(keep_record))
                        self.stdout.write(self.style.ERROR('Records to delete (older):'))
                        for record in delete_records:
                            self.stdout.write(self.format_record_info(record))
                    else:
                        # Delete records using their IDs
                        DikeRecord.objects.filter(id__in=delete_ids).delete()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nSummary: Would delete {total_duplicates} duplicate records.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully deleted {total_duplicates} duplicate records.'
            )) 