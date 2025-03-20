from django.core.management.base import BaseCommand
import os
import re
from siriuspasset.models import SpSlab as Slab, SpFossilSpecimen as Specimen, SpFossilImage as FossilImage, DirectoryScan, SpImageProcessingRecord
from django.core.files import File
from django.conf import settings
import hashlib
import time
import logging
from pathlib import Path
import shutil
from datetime import datetime

class Command(BaseCommand):
    help = 'Scan a designated directory for new images and import them'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Directory to scan for image files')
        parser.add_argument('--recursive', action='store_true', help='Scan subdirectories recursively')
        parser.add_argument('--prefix', type=str, help='Prefix to match (e.g., "SP")')
        parser.add_argument('--year', type=str, help='Year to match (e.g., "2016")')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')
        parser.add_argument('--slab-images-only', action='store_true', help='Process images as slab images only')
        parser.add_argument('--skip-existing', action='store_true', help='Skip existing images instead of updating them')
        parser.add_argument('--pattern', type=str, default='SP-', help='Pattern to match in filenames (e.g., SP-2016)')

    def handle(self, *args, **options):
        start_time = time.time()
        
        # Get options
        directory = options['directory']
        recursive = options['recursive']
        prefix = options['prefix']
        year = options['year']
        debug = options['debug']
        
        # Configure logging level
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.stdout.write(f'Scanning directory: {directory}')
        if recursive:
            self.stdout.write('Scanning recursively')
        if prefix and year:
            self.stdout.write(f'Looking for files matching prefix {prefix} and year {year}')
        
        # Create DirectoryScan record
        scan = DirectoryScan(
            directory=directory,
            recursive=recursive,
            prefix=prefix,
            year=year,
            status='started'
        )
        scan.save()
        
        try:
            # Get all slabs and specimens for quick lookup
            slabs = {slab.slab_no: slab for slab in Slab.objects.all()}
            specimens = {specimen.specimen_no: specimen for specimen in Specimen.objects.all()}
            
            # Get last successful scan time to skip older files
            last_scan = DirectoryScan.objects.filter(directory=directory, status='completed').order_by('-scan_end_time').first()
            last_scan_time = last_scan.scan_end_time if last_scan else None
            
            if last_scan_time and debug:
                self.stdout.write(f'Last successful scan was at {last_scan_time}')
            
            # Counters for summary
            found_files = 0
            processed_files = 0
            skipped_existing = 0
            skipped_duplicate = 0
            skipped_no_match = 0
            skipped_old = 0
            
            # Loop through all files in the directory
            for root, dirs, files in os.walk(directory):
                # Skip if not recursive and we're in a subdirectory
                if not recursive and root != directory:
                    continue
                
                for file in files:
                    # Only process image files
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        found_files += 1
                        image_path = os.path.join(root, file)
                        
                        # Skip files that haven't been modified since last scan
                        if last_scan_time:
                            mod_time = os.path.getmtime(image_path)
                            mod_datetime = datetime.fromtimestamp(mod_time)
                            if mod_datetime < last_scan_time:
                                skipped_old += 1
                                if debug:
                                    self.stdout.write(f'Skipping older file (not modified since last scan): {image_path}')
                                continue
                        
                        # Process the file
                        if self.process_file(image_path, slabs, specimens, prefix, year, debug):
                            processed_files += 1
            
            # Update scan record with successful completion
            scan.images_found = found_files
            scan.images_created = processed_files
            scan.log_summary = f"Found {found_files} files, processed {processed_files}, skipped {found_files - processed_files}"
            scan.mark_completed('completed')
            
            elapsed_time = time.time() - start_time
            
            # Print summary statistics
            self.stdout.write(self.style.SUCCESS(f'Scan completed in {elapsed_time:.2f} seconds'))
            self.stdout.write(f'Found {found_files} image files')
            self.stdout.write(f'Successfully processed {processed_files} images')
            if last_scan_time:
                self.stdout.write(f'Skipped {skipped_old} older files (not modified since last scan)')
            
            # Print summary of processing records
            record_count = SpImageProcessingRecord.objects.filter(command_used='scan_for_new_images').count()
            self.stdout.write(f'Created {record_count} processing records for tracking')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during scan: {str(e)}'))
            scan.log_summary = f"Scan failed with error: {str(e)}"
            scan.mark_completed('failed')

    def process_file(self, image_path, slabs, specimens, prefix=None, year=None, debug=False):
        """Process a single image file."""
        filename = os.path.basename(image_path)
        specimen = None
        slab = None
        file_hash = None
        
        # Calculate MD5 hash of the image file
        try:
            with open(image_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            error_msg = f'Error reading image file: {str(e)}'
            self.stdout.write(self.style.ERROR(f'{error_msg}: {image_path}'))
            
            # Track the error
            SpImageProcessingRecord.objects.create(
                original_path=image_path,
                filename=filename,
                status='error',
                status_message=error_msg,
                command_used='scan_for_new_images'
            )
            return False
        
        # Check if an image with this hash already exists
        if FossilImage.objects.filter(md5hash=file_hash).exists():
            duplicate_image = FossilImage.objects.filter(md5hash=file_hash).first()
            if debug:
                self.stdout.write(f'Image with hash {file_hash} already exists, skipping: {image_path}')
            
            # Track the duplicate
            SpImageProcessingRecord.objects.create(
                original_path=image_path,
                filename=filename,
                md5hash=file_hash,
                status='duplicate',
                status_message=f"Duplicate of existing image: {duplicate_image.image_file.name}",
                image=duplicate_image,
                slab=duplicate_image.slab,
                specimen=duplicate_image.specimen,
                command_used='scan_for_new_images'
            )
            return False
        
        # Check if an image with the same original path already exists
        if FossilImage.objects.filter(original_path=image_path).exists():
            existing_image = FossilImage.objects.filter(original_path=image_path).first()
            if debug:
                self.stdout.write(f'Image with this path already exists, skipping: {image_path}')
            
            # Track the existing path
            SpImageProcessingRecord.objects.create(
                original_path=image_path,
                filename=filename,
                md5hash=file_hash,
                status='skipped',
                status_message="Image with this path already exists in database",
                image=existing_image,
                slab=existing_image.slab,
                specimen=existing_image.specimen,
                command_used='scan_for_new_images'
            )
            return False
        
        # Create a clean version of the filename with whitespace removed for pattern matching
        clean_filename = filename.replace(" ", "")
        
        # Extract specimen or slab number from filename
        if prefix and year:
            # Pattern for specimens like SP-2016-0001A.jpg
            specimen_match = re.search(rf'{prefix}-{year}-(\d+)([A-Za-z])', clean_filename, re.IGNORECASE)
            
            # Pattern for slabs like SP-2016-0001.jpg
            slab_match = re.search(rf'{prefix}-{year}-(\d+)', clean_filename, re.IGNORECASE)
            
            if specimen_match:
                slab_number = specimen_match.group(1).zfill(4)
                specimen_letter = specimen_match.group(2).upper()
                slab_no = f"{prefix}-{year}-{slab_number}"
                specimen_no = f"{slab_no}-{specimen_letter}"
                
                # Find the slab
                if slab_no in slabs:
                    slab = slabs[slab_no]
                else:
                    slab = Slab.objects.filter(slab_no=slab_no).first()
                    if not slab:
                        self.stdout.write(self.style.WARNING(f'No slab found for number {slab_no}, creating new slab.'))
                        slab = Slab(slab_no=slab_no)
                        slab.save()
                        slabs[slab_no] = slab
                
                # Find the specimen
                if specimen_no in specimens:
                    specimen = specimens[specimen_no]
                else:
                    specimen = Specimen.objects.filter(specimen_no=specimen_no).first()
                    if not specimen:
                        self.stdout.write(self.style.WARNING(f'No specimen found for {specimen_no}, creating new specimen.'))
                        specimen = Specimen(specimen_no=specimen_no, slab=slab)
                        specimen.save()
                        specimens[specimen_no] = specimen
                
            elif slab_match:
                slab_number = slab_match.group(1).zfill(4)
                slab_no = f"{prefix}-{year}-{slab_number}"
                
                # Find the slab
                if slab_no in slabs:
                    slab = slabs[slab_no]
                else:
                    slab = Slab.objects.filter(slab_no=slab_no).first()
                    if not slab:
                        self.stdout.write(self.style.WARNING(f'No slab found for number {slab_no}, creating new slab.'))
                        slab = Slab(slab_no=slab_no)
                        slab.save()
                        slabs[slab_no] = slab
            else:
                self.stdout.write(self.style.WARNING(f"Could not parse filename: {filename} (clean version: {clean_filename})"))
                
                # Track the no-match file
                SpImageProcessingRecord.objects.create(
                    original_path=image_path,
                    filename=filename,
                    md5hash=file_hash,
                    status='no_match',
                    status_message=f"Could not parse filename pattern (clean version: {clean_filename})",
                    command_used='scan_for_new_images'
                )
                return False
        
        try:
            # Create a temporary copy of the image file
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, filename)
            shutil.copy2(image_path, temp_path)
            
            # Create a new image record
            with open(temp_path, 'rb') as f:
                image = FossilImage(
                    slab=slab,
                    specimen=specimen,
                    description='',
                    original_path=image_path,
                    md5hash=file_hash
                )
                
                # Save the image to create a record
                image.save()
                
                # Save the file
                image.image_file.save(filename, File(f), save=True)
                
                # Generate thumbnail
                thumbnail_created = False
                if image.generate_thumbnail():
                    thumbnail_created = True
                
                # Track the successful processing
                success_message = ""
                if specimen:
                    success_message = f"Created image for specimen {specimen.specimen_no}"
                    self.stdout.write(self.style.SUCCESS(f'{success_message}: {filename}'))
                else:
                    success_message = f"Created image for slab {slab.slab_no}"
                    self.stdout.write(self.style.SUCCESS(f'{success_message}: {filename}'))
                    
                SpImageProcessingRecord.objects.create(
                    original_path=image_path,
                    filename=filename,
                    md5hash=file_hash,
                    status='success',
                    status_message=f"{success_message}. Thumbnail: {'Created' if thumbnail_created else 'Failed'}",
                    image=image,
                    slab=slab,
                    specimen=specimen,
                    command_used='scan_for_new_images'
                )
            
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return True
                
        except Exception as e:
            error_msg = f'Error processing image file: {str(e)}'
            self.stdout.write(self.style.ERROR(f'{error_msg}: {image_path}'))
            
            # Track the error
            SpImageProcessingRecord.objects.create(
                original_path=image_path,
                filename=filename,
                md5hash=file_hash,
                status='error',
                status_message=error_msg,
                slab=slab,
                specimen=specimen,
                command_used='scan_for_new_images'
            )
            return False 