from django.core.management.base import BaseCommand
from siriuspasset.models import SpSlab, SpFossilSpecimen, SpFossilImage
import pandas as pd
from django.db import transaction, models
from collections import defaultdict
import os
import re
from pathlib import Path
from django.core.files import File
from django.conf import settings
import shutil
import hashlib
from siriuspasset.models import fossil_image_upload_path
import logging
from datetime import datetime

class Command(BaseCommand):
    help = 'Import specimens data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument('--no-delete', action='store_true', help='Do not delete existing records before import')
        parser.add_argument('--skip-existing', action='store_true', help='Skip existing records instead of updating them')
        parser.add_argument('--slab-images-only', action='store_true', help='Process images as slab images only')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        no_delete = options['no_delete']
        skip_existing = options['skip_existing']
        slab_images_only = options['slab_images_only']
        debug = options['debug']
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Extract prefix and year from filename
        filename = os.path.basename(excel_file)
        match = re.search(r'([A-Za-z]+)(\d{4})', filename)
        if match:
            prefix = match.group(1).upper()
            year = match.group(2)
            self.stdout.write(self.style.SUCCESS(f'Extracted prefix: {prefix}, year: {year} from filename'))
        else:
            self.stdout.write(self.style.ERROR(f'Could not extract prefix and year from filename: {filename}'))
            return
        
        # Delete existing records with the same prefix and year if not in no-delete mode
        if not no_delete and not skip_existing:
            self.delete_existing_records(prefix, year)
        
        # Read Excel file
        try:
            df = pd.read_excel(excel_file)
            self.stdout.write(self.style.SUCCESS(f'Successfully read Excel file with {len(df)} rows'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading Excel file: {str(e)}'))
            return
        
        # Process data
        with transaction.atomic():
            created_slabs, created_specimens = self.process_data(df, prefix, year, skip_existing, debug)
            
            # Process photos
            photo_dir = os.path.dirname(excel_file)
            created_images, skipped_images = self.process_specimen_photos(
                photo_dir, 
                created_slabs, 
                created_specimens, 
                prefix, 
                year, 
                skip_existing,
                slab_images_only,
                debug
            )
        
        self.stdout.write(self.style.SUCCESS(f'Import completed successfully'))
        self.stdout.write(f'Created {len(created_slabs)} slabs')
        self.stdout.write(f'Created {len(created_specimens)} specimens')
        self.stdout.write(f'Created {created_images} images')
        if skip_existing:
            self.stdout.write(f'Skipped {skipped_images} existing images')

    def delete_existing_records(self, prefix, year):
        """Delete existing records with the same prefix and year"""
        # Delete specimens first due to foreign key constraints
        slab_pattern = f'{prefix}{year}%'
        
        # Count existing records
        existing_specimens = SpFossilSpecimen.objects.filter(slab__slab_no__startswith=f'{prefix}{year}').count()
        existing_slabs = SpSlab.objects.filter(slab_no__startswith=f'{prefix}{year}').count()
        existing_images = SpFossilImage.objects.filter(
            models.Q(specimen__slab__slab_no__startswith=f'{prefix}{year}') | 
            models.Q(slab__slab_no__startswith=f'{prefix}{year}')
        ).count()
        
        self.stdout.write(f'Deleting {existing_specimens} existing specimens')
        self.stdout.write(f'Deleting {existing_slabs} existing slabs')
        self.stdout.write(f'Deleting {existing_images} existing images')
        
        # Delete specimens (this will cascade delete images)
        SpFossilSpecimen.objects.filter(slab__slab_no__startswith=f'{prefix}{year}').delete()
        
        # Delete slabs (this will cascade delete any remaining images)
        SpSlab.objects.filter(slab_no__startswith=f'{prefix}{year}').delete()

    def process_data(self, df, prefix, year, skip_existing, debug):
        """Process data from Excel file and create records"""
        created_slabs = {}  # Dictionary to store created slabs by slab_no
        created_specimens = {}  # Dictionary to store created specimens by specimen_no
        
        # Process each row in the dataframe
        for index, row in df.iterrows():
            # Extract slab number
            slab_no_raw = str(row.get('슬랩번호', ''))
            if not slab_no_raw or pd.isna(slab_no_raw):
                self.stdout.write(self.style.WARNING(f'Row {index+2}: Missing slab number, skipping'))
                continue
            
            # Format slab number to ensure it has 4 digits
            slab_no_match = re.search(r'(\d+)', slab_no_raw)
            if slab_no_match:
                slab_number = slab_no_match.group(1)
                # Pad to 4 digits
                slab_number = slab_number.zfill(4)
                slab_no = f"{prefix}{year}{slab_number}"
            else:
                self.stdout.write(self.style.WARNING(f'Row {index+2}: Invalid slab number format: {slab_no_raw}, skipping'))
                continue
            
            # Check if slab already exists
            if skip_existing and SpSlab.objects.filter(slab_no=slab_no).exists():
                if debug:
                    self.stdout.write(f'Slab {slab_no} already exists, using existing slab')
                slab = SpSlab.objects.get(slab_no=slab_no)
                created_slabs[slab_no] = slab
            else:
                # Create or get slab
                if slab_no in created_slabs:
                    slab = created_slabs[slab_no]
                else:
                    # Extract slab data
                    size_x = row.get('슬랩크기_가로', None)
                    size_y = row.get('슬랩크기_세로', None)
                    thickness = row.get('슬랩두께', None)
                    location = row.get('산지', '')
                    description = row.get('슬랩설명', '')
                    notes = row.get('비고', '')
                    
                    # Handle NaN values
                    if pd.isna(size_x): size_x = None
                    if pd.isna(size_y): size_y = None
                    if pd.isna(thickness): thickness = None
                    if pd.isna(location): location = ''
                    if pd.isna(description): description = ''
                    if pd.isna(notes): notes = ''
                    
                    # Create slab
                    slab = SpSlab(
                        slab_no=slab_no,
                        size_x=size_x,
                        size_y=size_y,
                        thickness=thickness,
                        location=location,
                        description=description,
                        notes=notes
                    )
                    slab.save()
                    created_slabs[slab_no] = slab
                    if debug:
                        self.stdout.write(f'Created slab: {slab_no}')
            
            # Extract specimen number
            specimen_no_raw = str(row.get('표본번호', ''))
            if not specimen_no_raw or pd.isna(specimen_no_raw):
                self.stdout.write(self.style.WARNING(f'Row {index+2}: Missing specimen number, skipping'))
                continue
            
            # Format specimen number
            specimen_no_match = re.search(r'(\d+)([A-Za-z])?', specimen_no_raw)
            if specimen_no_match:
                specimen_number = specimen_no_match.group(1)
                # Pad to 3 digits
                specimen_number = specimen_number.zfill(3)
                # Add suffix if present
                suffix = specimen_no_match.group(2) if specimen_no_match.group(2) else ''
                specimen_no = f"{prefix}{year}{slab_number}-{specimen_number}{suffix}"
            else:
                self.stdout.write(self.style.WARNING(f'Row {index+2}: Invalid specimen number format: {specimen_no_raw}, skipping'))
                continue
            
            # Check if specimen already exists
            if skip_existing and SpFossilSpecimen.objects.filter(specimen_no=specimen_no).exists():
                if debug:
                    self.stdout.write(f'Specimen {specimen_no} already exists, using existing specimen')
                specimen = SpFossilSpecimen.objects.get(specimen_no=specimen_no)
                created_specimens[specimen_no] = specimen
                continue
            
            # Extract specimen data
            name_kr = row.get('분류명_국명', '')
            name_en = row.get('분류명_학명', '')
            taxon = row.get('분류', '')
            description = row.get('표본설명', '')
            
            # Handle NaN values
            if pd.isna(name_kr): name_kr = ''
            if pd.isna(name_en): name_en = ''
            if pd.isna(taxon): taxon = ''
            if pd.isna(description): description = ''
            
            # Create specimen
            specimen = SpFossilSpecimen(
                specimen_no=specimen_no,
                slab=slab,
                name_kr=name_kr,
                name_en=name_en,
                taxon=taxon,
                description=description
            )
            specimen.save()
            created_specimens[specimen_no] = specimen
            if debug:
                self.stdout.write(f'Created specimen: {specimen_no}')
        
        return created_slabs, created_specimens

    def process_specimen_photos(self, photo_dir, slabs, specimens, prefix, year, skip_existing, slab_images_only, debug):
        """Process specimen photos and associate them with specimens"""
        created_count = 0
        skipped_existing_count = 0
        skipped_duplicate_count = 0
        
        # Get all image files in the directory and subdirectories
        image_files = []
        
        # Only search in directories that match the prefix-year pattern
        prefix_year = f"{prefix}{year}"
        
        for root, dirs, files in os.walk(photo_dir):
            # Check if this directory or any parent directory contains the prefix-year
            rel_path = os.path.relpath(root, photo_dir)
            if prefix_year.lower() in rel_path.lower() or rel_path == '.':
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        image_files.append(os.path.join(root, file))
        
        if debug:
            self.stdout.write(f'Found {len(image_files)} image files in directories matching {prefix_year}')
        
        # Process each image file
        for image_path in image_files:
            # Calculate MD5 hash of the image file
            with open(image_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check if an image with this hash already exists
            if SpFossilImage.objects.filter(md5hash=file_hash).exists():
                if debug:
                    self.stdout.write(f'Image with hash {file_hash} already exists, skipping: {image_path}')
                skipped_duplicate_count += 1
                continue
            
            # Extract specimen or slab number from filename
            filename = os.path.basename(image_path)
            
            # Try to match specimen pattern first (e.g., ABC2023XXXX-YYY)
            specimen_match = re.search(rf'{prefix_year}(\d+)-(\d+[A-Za-z]?)', filename, re.IGNORECASE)
            
            # If slab_images_only is True or no specimen match, try to match slab pattern (e.g., ABC2023XXXX)
            slab_match = None
            if slab_images_only or not specimen_match:
                slab_match = re.search(rf'{prefix_year}(\d+)', filename, re.IGNORECASE)
            
            # Determine if this is a specimen or slab image
            specimen = None
            slab = None
            
            if specimen_match and not slab_images_only:
                # This is a specimen image
                slab_number = specimen_match.group(1).zfill(4)
                specimen_number = specimen_match.group(2)
                
                # Format specimen number
                specimen_no_match = re.search(r'(\d+)([A-Za-z])?', specimen_number)
                if specimen_no_match:
                    specimen_number = specimen_no_match.group(1).zfill(3)
                    suffix = specimen_no_match.group(2) if specimen_no_match.group(2) else ''
                    specimen_no = f"{prefix}{year}{slab_number}-{specimen_number}{suffix}"
                    
                    # Find the specimen
                    if specimen_no in specimens:
                        specimen = specimens[specimen_no]
                        slab = specimen.slab
                    else:
                        if debug:
                            self.stdout.write(f'Specimen {specimen_no} not found for image: {image_path}')
                        continue
                else:
                    if debug:
                        self.stdout.write(f'Invalid specimen number format in filename: {filename}')
                    continue
            elif slab_match:
                # This is a slab image
                slab_number = slab_match.group(1).zfill(4)
                slab_no = f"{prefix}{year}{slab_number}"
                
                # Find the slab
                if slab_no in slabs:
                    slab = slabs[slab_no]
                else:
                    if debug:
                        self.stdout.write(f'Slab {slab_no} not found for image: {image_path}')
                    continue
            else:
                if debug:
                    self.stdout.write(f'Could not extract specimen or slab number from filename: {filename}')
                continue
            
            # Check if this image already exists in the expected directory
            if skip_existing:
                # Determine the expected path
                if specimen:
                    expected_path = fossil_image_upload_path(SpFossilImage(specimen=specimen), filename)
                else:
                    expected_path = fossil_image_upload_path(SpFossilImage(slab=slab), filename)
                
                full_expected_path = os.path.join(settings.MEDIA_ROOT, expected_path)
                
                # Check if the file exists and if there's a database record
                if os.path.exists(full_expected_path):
                    # Check if there's a database record for this image
                    if specimen:
                        existing_image = SpFossilImage.objects.filter(
                            specimen=specimen,
                            image_file__endswith=filename
                        ).first()
                    else:
                        existing_image = SpFossilImage.objects.filter(
                            slab=slab,
                            image_file__endswith=filename
                        ).first()
                    
                    if existing_image:
                        if debug:
                            self.stdout.write(f'Image already exists in database and filesystem, skipping: {image_path}')
                        skipped_existing_count += 1
                        continue
            
            # Create a temporary copy of the image file
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, filename)
            shutil.copy2(image_path, temp_path)
            
            # Create image record
            with open(temp_path, 'rb') as f:
                image = SpFossilImage(
                    specimen=specimen,
                    slab=slab,
                    description='',
                    original_path=image_path,
                    md5hash=file_hash
                )
                image.image_file.save(filename, File(f), save=False)
                image.save()
            
            # Clean up temporary file
            os.remove(temp_path)
            
            created_count += 1
            if debug:
                if specimen:
                    self.stdout.write(f'Created image for specimen {specimen.specimen_no}: {filename}')
                else:
                    self.stdout.write(f'Created image for slab {slab.slab_no}: {filename}')
        
        self.stdout.write(f'Created {created_count} images')
        self.stdout.write(f'Skipped {skipped_duplicate_count} duplicate images (based on MD5 hash)')
        if skip_existing:
            self.stdout.write(f'Skipped {skipped_existing_count} existing images')
        
        return created_count, skipped_duplicate_count + skipped_existing_count 