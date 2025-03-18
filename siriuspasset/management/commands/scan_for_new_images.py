from django.core.management.base import BaseCommand
from siriuspasset.models import SpSlab, SpFossilSpecimen, SpFossilImage, DirectoryScan
import os
import re
import hashlib
from django.conf import settings
from django.core.files import File
from django.utils import timezone
import time
import logging

class Command(BaseCommand):
    help = 'Scan a designated directory for new images and import them'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Path to the base directory to scan')
        parser.add_argument('--pattern', type=str, default='SP-', help='Pattern to match in filenames (e.g., SP-2016)')
        parser.add_argument('--skip-existing', action='store_true', help='Skip existing images instead of updating them')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')
        parser.add_argument('--slab-images-only', action='store_true', help='Process images as slab images only')

    def handle(self, *args, **options):
        directory = options['directory']
        pattern = options['pattern']
        skip_existing = options.get('skip_existing', False)
        debug = options.get('debug', False)
        slab_images_only = options.get('slab_images_only', False)
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Create a new scan record
        scan = DirectoryScan(
            scan_directory=directory,
            scan_pattern=pattern,
            status='in_progress'
        )
        scan.save()
        
        try:
            start_time = time.time()
            self.stdout.write(self.style.SUCCESS(f'Starting scan of {directory} with pattern {pattern}'))
            
            # Get all slabs and specimens for quick lookup
            slabs = {slab.slab_no: slab for slab in SpSlab.objects.all()}
            specimens = {specimen.specimen_no: specimen for specimen in SpFossilSpecimen.objects.all()}
            
            # Get last successful scan time to skip older files
            last_successful_scan = DirectoryScan.objects.filter(
                scan_directory=directory, 
                status='completed'
            ).order_by('-scan_end_time').first()
            
            last_scan_time = None
            if last_successful_scan:
                last_scan_time = last_successful_scan.scan_end_time
                self.stdout.write(f"Last successful scan completed at: {last_scan_time}")
            
            # Track statistics
            total_files = 0
            new_images = 0
            skipped_existing = 0
            skipped_duplicate = 0
            skipped_older = 0
            errors = 0
            log_entries = []
            
            # Walk through the directory tree
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        total_files += 1
                        
                        try:
                            # Full path to the image file
                            image_path = os.path.join(root, file)
                            
                            # Check if the file is older than the last scan
                            if last_scan_time:
                                file_creation_time = os.path.getctime(image_path)
                                file_modification_time = os.path.getmtime(image_path)
                                # Use the newer of creation or modification time
                                file_time = max(file_creation_time, file_modification_time)
                                file_time = timezone.datetime.fromtimestamp(file_time, tz=timezone.get_current_timezone())
                                
                                if file_time < last_scan_time:
                                    skipped_older += 1
                                    if debug:
                                        log_entries.append(f"Skipping older file: {file} (created before last scan)")
                                    continue
                            
                            # Check if the filename matches the pattern
                            if pattern not in file:
                                log_entries.append(f"Skipping {file}: Does not match pattern {pattern}")
                                continue
                            
                            # Calculate MD5 hash of the image file
                            with open(image_path, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                            
                            # Check if an image with this hash already exists
                            if SpFossilImage.objects.filter(md5hash=file_hash).exists():
                                skipped_duplicate += 1
                                if debug:
                                    log_entries.append(f"Skipping duplicate: {file} (hash: {file_hash})")
                                continue
                            
                            # Check if an image with the same original path already exists
                            if SpFossilImage.objects.filter(original_path=image_path).exists():
                                skipped_existing += 1
                                if debug:
                                    log_entries.append(f"Skipping existing: {file} (path: {image_path})")
                                continue
                            
                            # Extract specimen or slab number from filename
                            slab_match = None
                            if pattern.startswith('SP-'):
                                # Try various patterns for SP files
                                # Updated pattern to handle SP-YYYY-N[Letter]-PhotoNumber format
                                year_pattern = r'(SP-\d{4})-(\d+[A-Za-z]?)(?:-(\d+))?\.'  # e.g., SP-2016-1A-157.JPG
                                
                                # Check for slab pattern with parentheses
                                slab_parentheses_match = re.search(rf'(SP-\d{{4}}-\d+)\((\w+)\)', file, re.IGNORECASE)
                                if slab_parentheses_match:
                                    slab_no = slab_parentheses_match.group(1)
                                    view_type = slab_parentheses_match.group(2)  # dorsal, ventral, etc.
                                    slab = slabs.get(slab_no)
                                    specimen = None
                                    self.stdout.write(f"Found slab image: {file} -> {slab_no} ({view_type} view)")
                                else:
                                    # Standard pattern matching
                                    match = re.search(year_pattern, file, re.IGNORECASE)
                                    if match:
                                        prefix_year = match.group(1)  # e.g., SP-2016
                                        id_part = match.group(2)      # e.g., 1A or 1
                                        photo_num = match.group(3) if match.group(3) else ""  # e.g., 157
                                        
                                        # Check if the id_part has a letter (indicating a specimen)
                                        if re.search(r'[A-Za-z]', id_part):
                                            # This is a specimen (e.g., SP-2016-1A-157.JPG)
                                            # Split the number and letter parts
                                            slab_part = re.match(r'(\d+)', id_part).group(1)
                                            specimen_letter = id_part[len(slab_part):]  # Extract the letter part
                                            
                                            # Construct the slab number from the prefix and the digit part with zero padding
                                            slab_no = f"{prefix_year}-{int(slab_part):04d}"
                                            # Construct the specimen number
                                            specimen_no = f"{slab_no}-{specimen_letter}"
                                            
                                            # Find the specimen
                                            specimen = specimens.get(specimen_no)
                                            slab = slabs.get(slab_no)
                                            if specimen:
                                                self.stdout.write(f"Found specimen image: {file} -> {specimen_no} (photo #{photo_num})")
                                            else:
                                                self.stdout.write(self.style.WARNING(f"Specimen not found: {specimen_no} for {file}"))
                                                errors += 1
                                                continue
                                        else:
                                            # This is a slab (e.g., SP-2016-1-157.JPG)
                                            # Zero-pad the slab number to 4 digits
                                            slab_no = f"{prefix_year}-{int(id_part):04d}"
                                            slab = slabs.get(slab_no)
                                            specimen = None
                                            if slab:
                                                self.stdout.write(f"Found slab image: {file} -> {slab_no} (photo #{photo_num})")
                                            else:
                                                self.stdout.write(self.style.WARNING(f"Slab not found: {slab_no} for {file}"))
                                                errors += 1
                                                continue
                                    else:
                                        self.stdout.write(self.style.WARNING(f"Could not parse filename: {file}"))
                                        errors += 1
                                        continue
                            else:
                                # Handle other patterns if needed
                                self.stdout.write(self.style.WARNING(f"Unsupported pattern: {pattern}"))
                                errors += 1
                                continue
                            
                            # If slab_images_only is set, only process slab images
                            if slab_images_only and specimen is not None:
                                self.stdout.write(f"Skipping specimen image in slab-only mode: {file}")
                                continue
                            
                            # Create a new image record
                            image = SpFossilImage(
                                slab=slab,
                                specimen=specimen,
                                description='',
                                original_path=image_path,
                                md5hash=file_hash
                            )
                            
                            # Save the image to the database
                            with open(image_path, 'rb') as f:
                                image.save()
                                image.image_file.save(file, File(f), save=True)
                            
                            # Generate thumbnail
                            image.generate_thumbnail()
                            
                            new_images += 1
                            log_entries.append(f"Imported: {file}")
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error processing {file}: {str(e)}"))
                            errors += 1
                            log_entries.append(f"Error with {file}: {str(e)}")
            
            # Update the scan record
            scan.total_files_found = total_files
            scan.new_images_imported = new_images
            scan.duplicate_images_skipped = skipped_duplicate
            scan.existing_images_skipped = skipped_existing
            scan.older_files_skipped = skipped_older
            scan.error_count = errors
            scan.log_summary = "\n".join(log_entries[-100:])  # Keep the last 100 log entries
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Print summary
            self.stdout.write(self.style.SUCCESS(f"Scan completed in {duration:.2f} seconds"))
            self.stdout.write(f"Total files found: {total_files}")
            self.stdout.write(f"New images imported: {new_images}")
            self.stdout.write(f"Duplicate images skipped: {skipped_duplicate}")
            self.stdout.write(f"Existing images skipped: {skipped_existing}")
            self.stdout.write(f"Older files skipped: {skipped_older}")
            self.stdout.write(f"Errors: {errors}")
            
            scan.mark_completed('completed')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Scan failed: {str(e)}"))
            scan.log_summary = f"Scan failed with error: {str(e)}"
            scan.mark_completed('failed') 