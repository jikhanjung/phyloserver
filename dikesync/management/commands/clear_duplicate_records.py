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
                # Get all records with these values
                records = DikeRecord.objects.filter(
                    lat_1=dup['lat_1'],
                    lng_1=dup['lng_1'],
                    angle=dup['angle'],
                    distance=dup['distance']
                ).order_by('modified_date')  # Keep the most recently modified record

                # Get the IDs of records to keep and delete
                keep_id = records.first().id
                delete_ids = list(records.exclude(id=keep_id).values_list('id', flat=True))
                
                if delete_ids:
                    records_to_delete.extend(records.filter(id__in=delete_ids))
                    total_duplicates += len(delete_ids)

                    if not dry_run:
                        # Delete records using their IDs
                        DikeRecord.objects.filter(id__in=delete_ids).delete()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'Would delete {total_duplicates} duplicate records:'
            ))
            for record in records_to_delete:
                self.stdout.write(
                    f'  - ID: {record.id}, '
                    f'Location: ({record.lat_1}, {record.lng_1}), '
                    f'Angle: {record.angle}, '
                    f'Distance: {record.distance}'
                )
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully deleted {total_duplicates} duplicate records.'
            )) 