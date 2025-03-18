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
        parser.add_argument('excel_file', type=str, nargs='?', help='Path to the Excel file')
        parser.add_argument('--no-delete', action='store_true', help='Do not delete existing records before import')
        parser.add_argument('--skip-existing', action='store_true', help='Skip existing records instead of updating them')
        parser.add_argument('--slab-images-only', action='store_true', help='Process images as slab images only')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')
        parser.add_argument('--delete-all', action='store_true', help='Delete all specimens, slabs, and images data')

    def handle(self, *args, **options):
        delete_all = options['delete_all']
        debug = options['debug']
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # If delete_all is specified, delete all data and exit
        if delete_all:
            self.delete_all_records()
            return
            
        # Check if excel_file is provided when not using delete_all
        excel_file = options['excel_file']
        if not excel_file:
            self.stdout.write(self.style.ERROR('Excel file path is required when not using --delete-all'))
            return
            
        no_delete = options['no_delete']
        skip_existing = options['skip_existing']
        slab_images_only = options['slab_images_only']
        
        # Extract prefix and year from filename
        filename = os.path.basename(excel_file)
        match = re.search(r'([A-Za-z]+)[_\-]?(\d{4})', filename)
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
            
            # If no slabs were created, abort the process
            if not created_slabs:
                self.stdout.write(self.style.ERROR('No slabs were created. Import process aborted.'))
                return
                
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

    def delete_all_records(self):
        """Delete all specimens, slabs, and images data"""
        # Count existing records
        existing_specimens = SpFossilSpecimen.objects.count()
        existing_slabs = SpSlab.objects.count() 
        existing_images = SpFossilImage.objects.count()
        
        self.stdout.write(self.style.WARNING(f'WARNING: About to delete ALL data:'))
        self.stdout.write(self.style.WARNING(f'- {existing_specimens} specimens'))
        self.stdout.write(self.style.WARNING(f'- {existing_slabs} slabs'))
        self.stdout.write(self.style.WARNING(f'- {existing_images} images'))
        
        # Ask for confirmation
        confirm = input("Are you sure you want to delete ALL data? Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
            return
        
        # Delete specimens (this will cascade delete images that belong to specimens)
        self.stdout.write(f'Deleting all specimens...')
        SpFossilSpecimen.objects.all().delete()
        
        # Delete slabs (this will cascade delete any remaining images)
        self.stdout.write(f'Deleting all slabs...')
        SpSlab.objects.all().delete()
        
        # Delete any orphaned images (those not connected to specimens or slabs)
        self.stdout.write(f'Deleting any orphaned images...')
        SpFossilImage.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'All data has been deleted successfully.'))

    def delete_existing_records(self, prefix, year):
        """Delete existing records with the same prefix and year"""
        # Delete specimens first due to foreign key constraints
        pattern = f'{prefix}-{year}-%'
        
        # Count existing records
        existing_specimens = SpFossilSpecimen.objects.filter(slab__slab_no__startswith=f'{prefix}-{year}-').count()
        existing_slabs = SpSlab.objects.filter(slab_no__startswith=f'{prefix}-{year}-').count()
        existing_images = SpFossilImage.objects.filter(
            models.Q(specimen__slab__slab_no__startswith=f'{prefix}-{year}-') | 
            models.Q(slab__slab_no__startswith=f'{prefix}-{year}-')
        ).count()
        
        self.stdout.write(f'Deleting {existing_specimens} existing specimens')
        self.stdout.write(f'Deleting {existing_slabs} existing slabs')
        self.stdout.write(f'Deleting {existing_images} existing images')
        
        # Delete specimens (this will cascade delete images)
        SpFossilSpecimen.objects.filter(slab__slab_no__startswith=f'{prefix}-{year}-').delete()
        
        # Delete slabs (this will cascade delete any remaining images)
        SpSlab.objects.filter(slab_no__startswith=f'{prefix}-{year}-').delete()

    def process_data(self, df, prefix, year, skip_existing, debug):
        """Process data from Excel file and create records"""
        created_slabs = {}  # Dictionary to store created slabs by slab_no
        created_specimens = {}  # Dictionary to store created specimens by specimen_no
        auto_specimen_counters = {}  # Dictionary to track auto-generated specimen numbers per slab
        
        # Define the exact Excel column headers we're looking for
        excel_headers = {
            'slab': 'slab no.',
            'specimen': 'specimen no.',
            'taxon': 'taxon name',
            'phylum': 'phylum',
            'horizon': 'horizon',
            'remarks': 'remarks',
            'counterpart': 'Counterpart?'
        }
        
        # Clean the dataframe - remove completely empty rows
        df = df.dropna(how='all')
        
        # Show summary of the Excel file
        total_rows = len(df)
        self.stdout.write(f"Excel file contains {total_rows} rows (excluding completely empty rows)")
        
        # Check if the slab column exists and has any non-empty values
        if excel_headers['slab'] not in df.columns:
            self.stdout.write(self.style.ERROR(f"Required column '{excel_headers['slab']}' not found in Excel file. Process aborted."))
            return {}, {}
            
        # Count rows with valid slab numbers and find the last valid row
        valid_slab_rows = 0
        last_valid_row = -1
        consecutive_empty_rows = 0
        max_empty_rows = 5  # Stop after this many consecutive empty rows
        
        for index, row in df.iterrows():
            slab_no_raw = row.get(excel_headers['slab'], '')
            is_empty = pd.isna(slab_no_raw) or str(slab_no_raw).strip() == ''
            
            if is_empty:
                consecutive_empty_rows += 1
                if consecutive_empty_rows >= max_empty_rows and last_valid_row >= 0:
                    # We've found the end of the valid data
                    self.stdout.write(f"Found {consecutive_empty_rows} consecutive empty rows after row {last_valid_row+2}, stopping.")
                    break
            else:
                consecutive_empty_rows = 0
                valid_slab_rows += 1
                last_valid_row = index
                
        if valid_slab_rows == 0:
            self.stdout.write(self.style.ERROR(f"No valid slab numbers found in the Excel file. Process aborted."))
            return {}, {}
            
        if last_valid_row >= 0:
            self.stdout.write(f"Last valid slab number found at row {last_valid_row+2} (Excel row number)")
            # Trim the dataframe to only include rows up to the last valid slab
            df = df.iloc[:last_valid_row+1]
        
        # print out summary of the excel file
        self.stdout.write(f"Excel file contains {len(df)} rows (excluding completely empty rows)")
        # pause for user approval
        input("Press Enter to continue...")


        # Map Excel columns to model fields
        slab_field_mapping = {
            excel_headers['slab']: 'slab_no',
            excel_headers['horizon']: 'horizon',
            excel_headers['counterpart']: 'counterpart'
        }
        
        specimen_field_mapping = {
            excel_headers['specimen']: 'specimen_no',
            excel_headers['taxon']: 'taxon_name',
            excel_headers['phylum']: 'phylum',
            excel_headers['remarks']: 'remarks',
            excel_headers['counterpart']: 'counterpart'
        }
        
        # Display Excel headers for debugging
        if debug:
            self.stdout.write("Expected Excel headers:")
            for key, header in excel_headers.items():
                self.stdout.write(f"  - '{header}'")
                
            self.stdout.write("Actual Excel headers found:")
            for col in df.columns:
                self.stdout.write(f"  - '{col}'")
                
            self.stdout.write("Mapping to fields:")
            for excel_field, model_field in slab_field_mapping.items():
                if excel_field in df.columns:
                    self.stdout.write(f"  - '{excel_field}' → Slab.{model_field}")
                else:
                    self.stdout.write(f"  - WARNING: '{excel_field}' not found in Excel")
            
            for excel_field, model_field in specimen_field_mapping.items():
                if excel_field in df.columns:
                    self.stdout.write(f"  - '{excel_field}' → Specimen.{model_field}")
                else:
                    self.stdout.write(f"  - WARNING: '{excel_field}' not found in Excel")
        
        # Process each row in the dataframe
        for index, row in df.iterrows():
            # Extract slab number using the exact column header
            slab_no_raw = row.get(excel_headers['slab'], '')
            print(f"slab_no_raw: {slab_no_raw}")
            
            # print out the row number and the slab number
            self.stdout.write(f"Row {index+2}: {slab_no_raw}")
            #print row
            #self.stdout.write(f"{row}")
            

            # Skip entirely empty rows
            if all(pd.isna(value) or str(value).strip() == '' for value in row):
                if debug:
                    self.stdout.write(f"Row {index+2}: Skipping completely empty row")
                continue
            
            if pd.isna(slab_no_raw) or str(slab_no_raw).strip() == '':
                self.stdout.write(self.style.WARNING(f"Row {index+2}: Missing slab number in '{excel_headers['slab']}' column, skipping"))
                continue
            
            # Handle float conversion for number-only values (Excel reads numbers as floats)
            if isinstance(slab_no_raw, float) and slab_no_raw.is_integer():
                slab_no_raw = int(slab_no_raw)
                self.stdout.write(f"Converting float to integer: {slab_no_raw}")
            
            # Ensure the slab number is a string
            slab_no_raw = str(slab_no_raw)
            
            # Check if the slab number is just a number without prefix-year
            if re.match(r'^\d+$', slab_no_raw) or re.match(r'^\d+\.0$', slab_no_raw):
                # It's just a number, use prefix and year from filename
                # Remove any decimal part (like .0) if present
                if '.' in slab_no_raw:
                    slab_no_raw = slab_no_raw.split('.')[0]
                    
                slab_number = slab_no_raw.strip().zfill(4)  # Pad to 4 digits
                slab_no = f"{prefix}-{year}-{slab_number}"
                self.stdout.write(self.style.SUCCESS(f'Auto-completed slab number from {slab_no_raw} to {slab_no}'))
            # Regular SP-YYYY-N format
            elif re.match(r'^SP-\d{4}-\d+$', slab_no_raw):
                # Extract raw number, removing any year prefixes
                slab_no_match = re.search(r'(\w+)-(\d+)-(\d+)', slab_no_raw)
                if slab_no_match:
                    extracted_prefix = slab_no_match.group(1)
                    extracted_year = slab_no_match.group(2)
                    slab_number = slab_no_match.group(3)
                    
                    # if the year is not the same as the year in the filename, skip the row
                    if extracted_year != year:
                        self.stdout.write(self.style.WARNING(f"Row {index+2}: Year in slab number ({extracted_year}) doesn't match filename year ({year}), skipping"))
                        continue
                    
                    # if the prefix is not the same as the prefix in the filename, skip the row
                    if extracted_prefix != prefix:
                        self.stdout.write(self.style.WARNING(f"Row {index+2}: Prefix in slab number ({extracted_prefix}) doesn't match filename prefix ({prefix}), skipping"))
                        continue

                    # if the slab number is not a number, skip the row
                    if not slab_number.isdigit():
                        self.stdout.write(self.style.WARNING(f"Row {index+2}: Invalid slab number part: {slab_number}, skipping"))
                        continue
                    
                    # format the slab number to 4 digits
                    slab_number = slab_number.zfill(4)

                    slab_no = f"{prefix}-{year}-{slab_number}"
                else:
                    self.stdout.write(self.style.WARNING(f'Row {index+2}: Invalid slab number format: {slab_no_raw}, skipping'))
                    continue
            else:
                self.stdout.write(self.style.WARNING(f'Row {index+2}: Invalid slab number format: {slab_no_raw}, skipping'))
                continue
            
            # Check if slab already exists
            if skip_existing and SpSlab.objects.filter(slab_no=slab_no).exists():
                slab = SpSlab.objects.get(slab_no=slab_no)
                created_slabs[slab_no] = slab
                self.stdout.write(f'Using existing slab: {slab_no}')
                if debug:
                    self.stdout.write(f'  - Slab already exists in database')
            else:
                # Create or get slab
                if slab_no in created_slabs:
                    slab = created_slabs[slab_no]
                else:
                    # Extract slab data explicitly from each column
                    slab_data = {
                        'slab_no': slab_no  # We already processed this
                    }
                    
                    # Add horizon if it exists in the Excel file
                    if excel_headers['horizon'] in df.columns:
                        horizon = row.get(excel_headers['horizon'], '')
                        if not pd.isna(horizon):
                            slab_data['horizon'] = horizon
                    
                    # Add counterpart if it exists in the Excel file
                    if excel_headers['counterpart'] in df.columns:
                        counterpart = row.get(excel_headers['counterpart'], '')
                        if not pd.isna(counterpart):
                            slab_data['counterpart'] = counterpart
                    
                    # Create slab with the extracted data
                    slab = SpSlab(**slab_data)
                    slab.save()
                    created_slabs[slab_no] = slab
                    # Print slab creation result
                    self.stdout.write(self.style.SUCCESS(f'Created slab: {slab_no}'))
                    if debug:
                        self.stdout.write(f'  - Data: {slab_data}')
            
            # Extract specimen number using the exact column header
            specimen_no_raw = row.get(excel_headers['specimen'], '')
            
            # If the specimen number is NaN or empty, generate a sequence number
            is_auto_generated = False
            if pd.isna(specimen_no_raw) or str(specimen_no_raw).strip() == '':
                # Initialize counter for this slab if not exists
                if slab_no not in auto_specimen_counters:
                    # Find the highest existing specimen number for this slab
                    existing_specimens = SpFossilSpecimen.objects.filter(
                        slab=slab
                    )
                    
                    # Get all used letters/letter combinations for this slab
                    used_letters = set()
                    if existing_specimens.exists():
                        for existing in existing_specimens:
                            # Extract the specimen identifier from the full number
                            parts = existing.specimen_no.split('-')
                            if len(parts) >= 4:  # Format should be PREFIX-YEAR-SLAB-SPECIMEN
                                specimen_identifier = parts[-1]
                                
                                # Check if it's a letter or letter combination (not a number)
                                if re.match(r'^[A-Za-z]+$', specimen_identifier):
                                    used_letters.add(specimen_identifier.upper())
                    
                    auto_specimen_counters[slab_no] = used_letters
                
                # Generate the next available letter in Excel style (A-Z, then AA, AB, etc)
                used_letters = auto_specimen_counters[slab_no]
                
                # Helper function to convert a number to Excel-style column letters
                def num_to_excel_col(n):
                    result = ""
                    while n > 0:
                        n, remainder = divmod(n - 1, 26)
                        result = chr(65 + remainder) + result
                    return result
                
                # Find the next available letter combination
                next_letter_index = 1
                while True:
                    specimen_letter = num_to_excel_col(next_letter_index)
                    if specimen_letter not in used_letters:
                        break
                    next_letter_index += 1
                
                # Add the used letter combination to the set
                auto_specimen_counters[slab_no].add(specimen_letter)
                
                # Extract parts from slab_no to build specimen_no
                slab_parts = slab_no.split('-')
                if len(slab_parts) >= 3:
                    specimen_no = f"{slab_parts[0]}-{slab_parts[1]}-{slab_parts[2]}-{specimen_letter}"
                else:
                    specimen_no = f"{slab_no}-{specimen_letter}"
                
                # Keep trying letters until we find an unused specimen number
                while SpFossilSpecimen.objects.filter(specimen_no=specimen_no, slab=slab).exists():
                    next_letter_index += 1
                    specimen_letter = num_to_excel_col(next_letter_index)
                    
                    auto_specimen_counters[slab_no].add(specimen_letter)
                    
                    # Extract parts from slab_no to build specimen_no
                    if len(slab_parts) >= 3:
                        specimen_no = f"{slab_parts[0]}-{slab_parts[1]}-{slab_parts[2]}-{specimen_letter}"
                    else:
                        specimen_no = f"{slab_no}-{specimen_letter}"
                
                is_auto_generated = True
                
                self.stdout.write(self.style.SUCCESS(f'Auto-generated specimen ID with Excel-style letter: {specimen_no} for slab {slab.slab_no}'))
                if debug:
                    self.stdout.write(f'  - Row {index+2}: No specimen number provided, generated automatically')
            else:
                # Ensure the specimen number is a string
                specimen_no_raw = str(specimen_no_raw)
                # trim whitespaces
                specimen_no_raw = specimen_no_raw.strip()
                
                # Handle various formats of specimen numbers (numbers, letters, or combinations)
                if re.match(r'^[A-Za-z]$', specimen_no_raw):
                    # If it's just a single letter (A, B, C, etc.), use it directly
                    specimen_number = specimen_no_raw
                    
                    # Extract parts from slab_no to build specimen_no
                    slab_parts = slab_no.split('-')
                    if len(slab_parts) >= 3:
                        specimen_no = f"{slab_parts[0]}-{slab_parts[1]}-{slab_parts[2]}-{specimen_number}"
                    else:
                        specimen_no = f"{slab_no}-{specimen_number}"
                else:
                    # Try to extract numeric and alphabetic parts
                    specimen_no_match = re.search(r'(\d+)([A-Za-z])?', specimen_no_raw)
                    if specimen_no_match:
                        specimen_number = specimen_no_match.group(1)
                        # Don't pad the number
                        suffix = specimen_no_match.group(2) if specimen_no_match.group(2) else ''
                        
                        # Extract parts from slab_no to build specimen_no
                        slab_parts = slab_no.split('-')
                        if len(slab_parts) >= 3:
                            specimen_no = f"{slab_parts[0]}-{slab_parts[1]}-{slab_parts[2]}-{specimen_number}{suffix}"
                        else:
                            specimen_no = f"{slab_no}-{specimen_number}{suffix}"
                    else:
                        self.stdout.write(self.style.WARNING(f'Row {index+2}: Invalid specimen number format: {specimen_no_raw}, skipping'))
                        continue
            
            # Extract specimen data explicitly from each column
            specimen_data = {
                'specimen_no': specimen_no,  # We already processed this
                'slab': slab  # We need this relationship
            }
            
            # Add taxon_name if it exists in the Excel file
            if excel_headers['taxon'] in df.columns:
                taxon_name = row.get(excel_headers['taxon'], '')
                if not pd.isna(taxon_name):
                    specimen_data['taxon_name'] = taxon_name
            
            # Add phylum if it exists in the Excel file
            if excel_headers['phylum'] in df.columns:
                phylum = row.get(excel_headers['phylum'], '')
                if not pd.isna(phylum):
                    specimen_data['phylum'] = phylum
            
            # Add remarks if it exists in the Excel file
            if excel_headers['remarks'] in df.columns:
                remarks = row.get(excel_headers['remarks'], '')
                if not pd.isna(remarks):
                    specimen_data['remarks'] = remarks
            
            # Add counterpart if it exists in the Excel file
            if excel_headers['counterpart'] in df.columns:
                counterpart = row.get(excel_headers['counterpart'], '')
                if not pd.isna(counterpart):
                    specimen_data['counterpart'] = counterpart
            
            # Check if specimen already exists
            if skip_existing and not is_auto_generated:
                existing_specimen = SpFossilSpecimen.objects.filter(specimen_no=specimen_no, slab=slab).first()
                if existing_specimen:
                    self.stdout.write(f'Using existing specimen: {specimen_no} for slab {slab.slab_no}')
                    if debug:
                        self.stdout.write(f'  - Specimen already exists in database')
                    created_specimens[specimen_no] = existing_specimen
                    continue
            elif not skip_existing:
                # When not skipping, check if we need to update an existing specimen
                existing_specimen = SpFossilSpecimen.objects.filter(specimen_no=specimen_no, slab=slab).first()
                if existing_specimen:
                    # Update existing specimen
                    for field, value in specimen_data.items():
                        if field not in ['specimen_no', 'slab']:  # Don't change the key fields
                            setattr(existing_specimen, field, value)
                    existing_specimen.save()
                    created_specimens[specimen_no] = existing_specimen
                    self.stdout.write(self.style.SUCCESS(f'Updated existing specimen: {specimen_no} for slab {slab.slab_no}'))
                    if debug:
                        self.stdout.write(f'  - Updated fields: {[f for f in specimen_data.keys() if f not in ["specimen_no", "slab"]]}')
                    continue
            
            # Create specimen with the extracted data
            specimen = SpFossilSpecimen(**specimen_data)
            specimen.save()
            created_specimens[specimen_no] = specimen
            # Print specimen creation result
            self.stdout.write(self.style.SUCCESS(f'Created specimen: {specimen_no} for slab {slab.slab_no}'))
            if debug:
                self.stdout.write(f'  - Data: {specimen_data}')
            
            # Print a separator line after each row
            self.stdout.write('-' * 80)
        
        # Report auto-generated specimens count
        total_auto_generated = sum(len(letters) for letters in auto_specimen_counters.values())
        if total_auto_generated > 0:
            self.stdout.write(f'Auto-generated {total_auto_generated} specimen numbers for rows with missing specimen numbers')
            
        return created_slabs, created_specimens

    def process_specimen_photos(self, photo_dir, slabs, specimens, prefix, year, skip_existing, slab_images_only, debug):
        """Process specimen photos and associate them with specimens"""
        created_count = 0
        skipped_existing_count = 0
        skipped_duplicate_count = 0
        skipped_no_prefix_count = 0
        skipped_no_match_count = 0
        thumbnail_count = 0
        
        # Get all image files in the directory and subdirectories
        image_files = []
        all_image_files = []
        
        # Print debug info about photo directory
        self.stdout.write(f'Looking for images in: {photo_dir}')
        self.stdout.write(f'Searching for pattern: {prefix}-{year}')
        
        # Pattern like "SP-2016"
        prefix_year_pattern = rf"{prefix}-{year}"
        
        for root, dirs, files in os.walk(photo_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    all_image_files.append(os.path.join(root, file))
                    # Only include files with the specific prefix-year pattern in the filename
                    if re.search(prefix_year_pattern, file, re.IGNORECASE):
                        image_files.append(os.path.join(root, file))
                    else:
                        skipped_no_prefix_count += 1
        
        # Print summary about found files
        self.stdout.write(f'Found {len(all_image_files)} total image files')
        self.stdout.write(f'Found {len(image_files)} image files matching pattern {prefix_year_pattern}')
        self.stdout.write(f'Skipped {skipped_no_prefix_count} images without the required pattern')
        
        if not image_files:
            self.stdout.write(self.style.WARNING(f'No images found with pattern {prefix_year_pattern}!'))
            if all_image_files and len(all_image_files) <= 10:
                self.stdout.write('Examples of image files found:')
                for img in all_image_files:
                    self.stdout.write(f'  - {os.path.basename(img)}')
            return 0, 0
        
        # Process each image file
        for image_path in image_files:
            # Calculate MD5 hash of the image file
            try:
                with open(image_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading image file: {image_path}. Error: {str(e)}'))
                continue
            
            # Check if an image with this hash already exists
            if SpFossilImage.objects.filter(md5hash=file_hash).exists():
                if debug:
                    self.stdout.write(f'Image with hash {file_hash} already exists, skipping: {image_path}')
                skipped_duplicate_count += 1
                continue
            
            # Extract specimen or slab number from filename
            filename = os.path.basename(image_path)
            self.stdout.write(f'Processing image: {filename}')
            
            # Check for slab images with parentheses patterns first: SP-2016-0001(dorsal).jpg or SP-2016-0001(ventral).jpg
            slab_parentheses_match = re.search(rf'{prefix}-{year}-(\d+)\((\w+)\)', filename, re.IGNORECASE)
            
            # Check for specimens with letter identifiers: SP-2016-0001A or SP-2016-0001A-2.jpg
            specimen_with_letter_match = re.search(rf'{prefix}-{year}-(\d+)([A-Za-z])(?:-\d+)?', filename, re.IGNORECASE)
            
            # All other patterns (including SP-2017-1003-2.JPG) should be treated as slab images
            # This will match patterns like SP-2016-0001.jpg and SP-2016-0001-2.jpg
            slab_match = re.search(rf'{prefix}-{year}-(\d+)(?:-\d+)?', filename, re.IGNORECASE)
            
            # Determine if this is a specimen or slab image
            specimen = None
            slab = None

            if slab_parentheses_match:
                # This is a slab image with (dorsal) or (ventral) notation
                slab_number = slab_parentheses_match.group(1).zfill(4)
                view_type = slab_parentheses_match.group(2)  # dorsal or ventral
                slab_no = f"{prefix}-{year}-{slab_number}"
                
                # Find the slab
                if slab_no in slabs:
                    slab = slabs[slab_no]
                    self.stdout.write(f'Matched to slab {slab_no} ({view_type} view)')
                else:
                    self.stdout.write(f'Slab {slab_no} not found in the database for image: {filename}')
                    # Try to find it in the database directly
                    try:
                        slab = SpSlab.objects.get(slab_no=slab_no)
                        self.stdout.write(f'Found slab {slab_no} in database instead')
                    except SpSlab.DoesNotExist:
                        if debug:
                            self.stdout.write(f'Slab {slab_no} not found in database either')
                        skipped_no_match_count += 1
                        continue
            elif specimen_with_letter_match and not slab_images_only:
                # This is a specimen image with a letter (e.g., SP-2016-0001A)
                slab_number = specimen_with_letter_match.group(1).zfill(4)
                specimen_letter = specimen_with_letter_match.group(2)
                specimen_no = f"{prefix}-{year}-{slab_number}-{specimen_letter}"
                
                # Find the specimen
                if specimen_no in specimens:
                    specimen = specimens[specimen_no]
                    slab = specimen.slab
                    self.stdout.write(f'Matched to specimen with letter: {specimen_no}')
                else:
                    self.stdout.write(f'Specimen {specimen_no} not found in the database for image: {filename}')
                    # Try to find it in the database directly
                    try:
                        specimen = SpFossilSpecimen.objects.get(specimen_no=specimen_no)
                        slab = specimen.slab
                        self.stdout.write(f'Found specimen {specimen_no} in database instead')
                    except SpFossilSpecimen.DoesNotExist:
                        if debug:
                            self.stdout.write(f'Specimen {specimen_no} not found in database either')
                        skipped_no_match_count += 1
                        continue
            elif slab_match:
                # This is a slab image (also handles SP-2017-1003-2.JPG as a slab image)
                slab_number = slab_match.group(1).zfill(4)
                slab_no = f"{prefix}-{year}-{slab_number}"
                
                # Find the slab
                if slab_no in slabs:
                    slab = slabs[slab_no]
                    self.stdout.write(f'Matched to slab: {slab_no}')
                else:
                    self.stdout.write(f'Slab {slab_no} not found in the database for image: {filename}')
                    # Try to find it in the database directly
                    try:
                        slab = SpSlab.objects.get(slab_no=slab_no)
                        self.stdout.write(f'Found slab {slab_no} in database instead')
                    except SpSlab.DoesNotExist:
                        if debug:
                            self.stdout.write(f'Slab {slab_no} not found in database either')
                        skipped_no_match_count += 1
                        continue
            else:
                if debug:
                    self.stdout.write(f'Could not extract specimen or slab number from filename: {filename}')
                skipped_no_match_count += 1
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
                        self.stdout.write(f'Image already exists in database and filesystem, skipping: {filename}')
                        skipped_existing_count += 1
                        continue
            
            # Create a temporary copy of the image file
            try:
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
                    
                    try:
                        # First save the image without the file to create the record
                        image.save()
                        # Then assign and save the file
                        image.image_file.save(filename, File(f), save=True)
                        
                        # Create thumbnail after saving the image
                        if image.generate_thumbnail():
                            thumbnail_count += 1
                            if debug:
                                self.stdout.write(f"Created thumbnail for {os.path.basename(image.image_file.name)}")
                        
                        created_count += 1
                        if specimen:
                            self.stdout.write(self.style.SUCCESS(f'Created image for specimen {specimen.specimen_no}: {filename}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Created image for slab {slab.slab_no}: {filename}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error saving image to database: {str(e)}'))
                        # If the image record was created but file save failed, clean up
                        if image.pk:
                            image.delete()
                
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing image file: {str(e)}'))
        
        # Print summary statistics
        self.stdout.write(self.style.SUCCESS(f'Processed {len(image_files)} image files:'))
        self.stdout.write(f'- Created {created_count} new images')
        self.stdout.write(f'- Created {thumbnail_count} thumbnails')
        self.stdout.write(f'- Skipped {skipped_duplicate_count} duplicate images (based on MD5 hash)')
        self.stdout.write(f'- Skipped {skipped_no_match_count} images with no matching slab/specimen')
        if skip_existing:
            self.stdout.write(f'- Skipped {skipped_existing_count} existing images')
        
        return created_count, skipped_duplicate_count + skipped_existing_count + skipped_no_match_count 