from django.core.management.base import BaseCommand
from siriuspasset.models import SpFossilImage
import os
import time

class Command(BaseCommand):
    help = 'Generate thumbnails for all images in the database'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force regenerate thumbnails even if they already exist')
        parser.add_argument('--limit', type=int, help='Limit number of thumbnails to generate')
        parser.add_argument('--specimen', type=str, help='Generate thumbnails only for a specific specimen number')
        parser.add_argument('--slab', type=str, help='Generate thumbnails only for a specific slab number')

    def handle(self, *args, **options):
        force = options.get('force', False)
        limit = options.get('limit')
        specimen_no = options.get('specimen')
        slab_no = options.get('slab')
        
        self.stdout.write(self.style.NOTICE('Starting thumbnail generation...'))
        
        # Build query based on options
        query = SpFossilImage.objects.all()
        
        if specimen_no:
            self.stdout.write(f'Filtering by specimen: {specimen_no}')
            query = query.filter(specimen__specimen_no=specimen_no)
            
        if slab_no:
            self.stdout.write(f'Filtering by slab: {slab_no}')
            query = query.filter(slab__slab_no=slab_no)
            
        if limit:
            self.stdout.write(f'Limiting to {limit} images')
            query = query[:limit]
            
        images = query.order_by('id')
        total_images = images.count()
        
        if total_images == 0:
            self.stdout.write(self.style.WARNING('No images found matching the criteria.'))
            return
            
        self.stdout.write(f'Found {total_images} images to process.')
        
        # Track statistics
        created_count = 0
        skipped_count = 0
        error_count = 0
        start_time = time.time()
        
        for i, image in enumerate(images, 1):
            try:
                # Check if thumbnail already exists
                thumbnail_path = image.get_thumbnail_path()
                
                if os.path.exists(thumbnail_path) and not force:
                    self.stdout.write(f'[{i}/{total_images}] Thumbnail already exists for {os.path.basename(image.image_file.name)}, skipping.')
                    skipped_count += 1
                    continue
                
                # Generate thumbnail
                if image.generate_thumbnail():
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[{i}/{total_images}] Created thumbnail for {os.path.basename(image.image_file.name)}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'[{i}/{total_images}] Failed to create thumbnail for {os.path.basename(image.image_file.name)}')
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'[{i}/{total_images}] Error processing {os.path.basename(image.image_file.name)}: {str(e)}')
                )
                
            # Print progress every 10 images
            if i % 10 == 0:
                elapsed = time.time() - start_time
                images_per_second = i / elapsed if elapsed > 0 else 0
                self.stdout.write(f'Progress: {i}/{total_images} ({round(i/total_images*100, 1)}%) - {round(images_per_second, 1)} images/sec')
        
        # Print summary
        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'\nThumbnail generation completed in {round(elapsed, 1)} seconds'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Errors: {error_count}') 