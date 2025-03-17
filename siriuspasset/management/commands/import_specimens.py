from django.core.management.base import BaseCommand
from siriuspasset.models import SpSlab, SpFossilSpecimen, SpFossilSpecimenImage
import pandas as pd
from django.db import transaction
from collections import defaultdict
import os
import re
from pathlib import Path
from django.core.files import File
from django.conf import settings
import shutil
import hashlib
from siriuspasset.models import fossil_image_upload_path

class Command(BaseCommand):
    help = 'Import specimens data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument('--no-delete', action='store_true', help='Skip deletion of existing records')
        parser.add_argument('--skip-existing', action='store_true', 
                           help='Skip modification if same entry already exists (incremental update)')

    def extract_prefix_year(self, filename):
        """Extract prefix and year from Excel filename."""
        # Pattern for filenames like "SP-2016_Catalog_compiled.xlsx"
        pattern = re.compile(r'([A-Z]+)-(\d{4}).*\.xlsx$')
        match = pattern.match(filename)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def format_slab_number(self, slab_no, prefix, year):
        """Format slab number with 4-digit zero padding."""
        # Extract the numeric part after PREFIX-YEAR-
        pattern = re.compile(f"{prefix}-{year}-(\d+).*")
        match = pattern.match(slab_no)
        if match:
            number = match.group(1)
            # Remove any leading zeros and format with 4 digits
            number = re.sub(r'^0+', '', number)
            return f"{prefix}-{year}-{int(number):04d}"
        return slab_no

    def delete_existing_records(self, prefix, year):
        """Delete all records for the given prefix and year."""
        pattern = f"{prefix}-{year}"
        
        # First, get all slabs matching the pattern
        slabs = SpSlab.objects.filter(slab_no__startswith=pattern)
        
        # Count records before deletion
        slab_count = slabs.count()
        specimen_count = SpFossilSpecimen.objects.filter(slab__in=slabs).count()
        image_count = SpFossilSpecimenImage.objects.filter(specimen__slab__in=slabs).count()
        
        # Delete slabs (this will cascade to specimens and images due to foreign key relationships)
        slabs.delete()
        
        return slab_count, specimen_count, image_count

    def calculate_md5(self, file_path):
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def custom_fossil_image_path(self, instance, filename):
        """
        Custom version of fossil_image_upload_path that preserves the original filename.
        Uses the original function but replaces the generated filename with the original.
        """
        # Get the path from the original function
        original_path = fossil_image_upload_path(instance, filename)
        
        # Extract the directory part (everything before the last /)
        directory = os.path.dirname(original_path)
        
        # Combine the directory with the original filename
        return os.path.join(directory, filename)

    def process_specimen_photos(self, base_path, specimens, prefix, year):
        """
        Process specimen photos in the directory structure.
        base_path: directory containing the Excel file and photo directories
        specimens: dict of specimens keyed by specimen_no for quick lookup
        prefix: prefix from Excel filename (e.g., 'SP')
        year: year from Excel filename (e.g., '2016')
        """
        # Print debug information about available specimens
        self.stdout.write(self.style.WARNING(f"Available specimen numbers: {list(specimens.keys())}"))
        
        # Pattern for filenames like:
        # "SP-2016-1A-1.JPG" or "SP-2016-1-1.JPG" (non-padded numbers)
        specimen_pattern = re.compile(r'(SP-\d{4})-(\d+)([A-Z]?)-(\d+)\.[Jj][Pp][Gg]')
        
        base_path = Path(base_path)
        photo_count = 0
        duplicate_count = 0
        skipped_existing_count = 0
        media_root = Path(settings.MEDIA_ROOT)
        
        # Pattern to match directories containing the prefix-year
        dir_pattern = f"{prefix}-{year}"

        # Debug: Print the base path being searched
        self.stdout.write(self.style.WARNING(f"Searching for photos in: {base_path}"))
        self.stdout.write(self.style.WARNING(f"Looking for directories containing: {dir_pattern}"))

        # First, find all matching directories
        matching_dirs = []
        for item in os.listdir(base_path):
            item_path = base_path / item
            if item_path.is_dir() and dir_pattern.lower() in item.lower():
                matching_dirs.append(item_path)
                self.stdout.write(self.style.SUCCESS(f"Found matching directory: {item_path}"))
        
        # If no matching directories found, check if the base directory itself contains images
        if not matching_dirs:
            self.stdout.write(self.style.WARNING(f"No matching directories found. Checking base directory."))
            # Check if the base directory contains any matching images
            jpg_files = [f for f in os.listdir(base_path) if f.lower().endswith('.jpg') and dir_pattern.lower() in f.lower()]
            if jpg_files:
                matching_dirs.append(base_path)
                self.stdout.write(self.style.SUCCESS(f"Found matching images in base directory: {len(jpg_files)} files"))
        
        # If still no matching directories, warn the user
        if not matching_dirs:
            self.stdout.write(self.style.WARNING(
                f"No directories or images matching '{dir_pattern}' found. "
                f"Please check that your photos are in a directory containing '{dir_pattern}' in its name."
            ))
            return 0

        # Process each matching directory
        for dir_path in matching_dirs:
            self.stdout.write(self.style.SUCCESS(f"Processing directory: {dir_path}"))
            
            # Walk through the directory and its subdirectories
            for root, dirs, files in os.walk(dir_path):
                # Debug: Print current directory being processed
                self.stdout.write(self.style.WARNING(f"Checking directory: {root}"))
                jpg_files = [f for f in files if f.lower().endswith('.jpg')]
                self.stdout.write(self.style.WARNING(f"Found files: {jpg_files}"))
                
                for filename in jpg_files:
                    file_path = Path(root) / filename
                    
                    # Debug: Print file being processed
                    self.stdout.write(self.style.WARNING(f"Processing file: {filename}"))
                    
                    # Calculate MD5 hash
                    md5hash = self.calculate_md5(file_path)
                    self.stdout.write(self.style.WARNING(f"MD5 hash: {md5hash}"))
                    
                    # Match the filename pattern before doing more intensive checks
                    match = specimen_pattern.match(filename)
                    if not match:
                        self.stdout.write(self.style.WARNING(
                            f"File {filename} did not match the expected pattern"
                        ))
                        continue
                        
                    prefix_year = match.group(1)  # SP-2016
                    slab_num = match.group(2)     # non-padded number
                    specimen_letter = match.group(3) or ''  # A, B, C, etc. or empty
                    sequence = match.group(4)      # photo sequence number
                    
                    # Format the slab number with zero padding
                    formatted_slab_no = f"{prefix_year}-{int(slab_num):04d}"
                    # Construct the full specimen ID as it appears in the database
                    specimen_id = f"{formatted_slab_no}-{specimen_letter}" if specimen_letter else formatted_slab_no
                    
                    # Debug: Print extracted information
                    self.stdout.write(self.style.WARNING(
                        f"Matched pattern - Prefix_Year: {prefix_year}, Slab: {slab_num}, "
                        f"Letter: {specimen_letter}, Sequence: {sequence}"
                    ))
                    self.stdout.write(self.style.WARNING(
                        f"Looking for specimen ID: {specimen_id}"
                    ))
                    
                    # Check if this hash already exists in the database (for all modes)
                    if SpFossilSpecimenImage.objects.filter(md5hash=md5hash).exists():
                        self.stdout.write(self.style.WARNING(
                            f"Skipping duplicate image: {filename} (MD5: {md5hash})"
                        ))
                        duplicate_count += 1
                        continue
                        
                    # Additional check for --skip-existing option
                    if self.command_options.get('skip_existing'):
                        # Create a dummy instance to get the expected path
                        dummy_specimen = None
                        for spec_id, spec in specimens.items():
                            if spec_id.lower() == specimen_id.lower():
                                dummy_specimen = spec
                                break
                                
                        if dummy_specimen:
                            dummy_image = SpFossilSpecimenImage(specimen=dummy_specimen)
                            expected_path = self.custom_fossil_image_path(dummy_image, filename)
                            full_expected_path = os.path.join(settings.MEDIA_ROOT, expected_path)
                            
                            # Check if file already exists in the expected location
                            if os.path.exists(full_expected_path):
                                # Also check if database record exists
                                if SpFossilSpecimenImage.objects.filter(
                                    specimen__specimen_no__iexact=specimen_id,
                                    image_file__endswith=filename
                                ).exists():
                                    self.stdout.write(self.style.WARNING(
                                        f"Skipping existing image file: {filename} (already exists in database and directory)"
                                    ))
                                    skipped_existing_count += 1
                                    continue
                    
                    # Find the corresponding specimen
                    specimen = None
                    # Try exact match first
                    if specimen_id in specimens:
                        specimen = specimens[specimen_id]
                        self.stdout.write(self.style.SUCCESS(f"Found exact match for {specimen_id}"))
                    else:
                        # Try matching without considering case
                        for spec_id, spec in specimens.items():
                            if spec_id.lower() == specimen_id.lower():
                                specimen = spec
                                self.stdout.write(self.style.SUCCESS(
                                    f"Found case-insensitive match: {specimen_id} -> {spec_id}"
                                ))
                                break
                    
                    if specimen:
                        try:
                            # Create a new SpFossilSpecimenImage instance
                            image = SpFossilSpecimenImage(
                                specimen=specimen,
                                description=f"Photo sequence {sequence}",
                                original_path=str(file_path),
                                md5hash=md5hash
                            )
                            
                            # Get the target path using our custom function
                            target_path = self.custom_fossil_image_path(image, filename)
                            
                            # Create the full path in the media directory
                            full_target_path = os.path.join(settings.MEDIA_ROOT, target_path)
                            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
                            
                            # Copy the file to the target location
                            shutil.copy2(file_path, full_target_path)
                            
                            # Set the image_file field to the relative path
                            image.image_file = target_path
                            image.save()

                            photo_count += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'Added photo {filename} to specimen {specimen_id} at {target_path}'
                            ))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f'Error processing photo {filename}: {str(e)}'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'No matching specimen found for photo {filename} (ID: {specimen_id})'
                        ))

        # Print summary
        summary = []
        if duplicate_count > 0:
            summary.append(f"Skipped {duplicate_count} duplicate images (based on MD5 hash)")
        if skipped_existing_count > 0:
            summary.append(f"Skipped {skipped_existing_count} existing images (in --skip-existing mode)")
        if summary:
            self.stdout.write(self.style.SUCCESS("\n".join(summary)))
            
        return photo_count

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        base_path = os.path.dirname(os.path.abspath(excel_file))
        
        # Store command options for access in other methods
        self.command_options = options
        
        # Extract prefix and year from filename
        filename = os.path.basename(excel_file)
        prefix, year = self.extract_prefix_year(filename)
        
        if not prefix or not year:
            self.stdout.write(self.style.ERROR(
                f'Could not extract prefix and year from filename {filename}. '
                'Expected format: PREFIX-YEAR_*.xlsx (e.g., SP-2016_Catalog_compiled.xlsx)'
            ))
            return
            
        try:
            with transaction.atomic():
                # Delete existing records if --no-delete and --skip-existing are not specified
                if not options['no_delete'] and not options['skip_existing']:
                    self.stdout.write(self.style.WARNING(
                        f'Deleting existing records for {prefix}-{year}...'
                    ))
                    slab_count, specimen_count, image_count = self.delete_existing_records(prefix, year)
                    self.stdout.write(self.style.SUCCESS(
                        f'Deleted {slab_count} slabs, {specimen_count} specimens, '
                        f'and {image_count} images for {prefix}-{year}'
                    ))
                
                # Read the Excel file
                df = pd.read_excel(excel_file)
                
                # Keep track of specimen count per slab for auto-numbering
                specimen_counters = defaultdict(int)
                # Dictionary to store specimens for photo processing
                specimens_dict = {}
                
                # Counters for statistics
                created_slabs = 0
                skipped_slabs = 0
                created_specimens = 0
                skipped_specimens = 0
                
                # Process each row in the dataframe
                for _, row in df.iterrows():
                    original_slab_no = row['slab no.']
                    # Format the slab number with 4 digits
                    slab_no = self.format_slab_number(original_slab_no, prefix, year)
                    
                    if slab_no != original_slab_no:
                        self.stdout.write(self.style.SUCCESS(
                            f'Formatted slab number: {original_slab_no} -> {slab_no}'
                        ))
                    
                    # Check if slab exists
                    existing_slab = None
                    if options['skip_existing']:
                        try:
                            existing_slab = SpSlab.objects.get(slab_no=slab_no)
                            skipped_slabs += 1
                            self.stdout.write(self.style.WARNING(
                                f'Skipping existing slab: {slab_no}'
                            ))
                        except SpSlab.DoesNotExist:
                            pass
                    
                    # Get or create the slab
                    if existing_slab:
                        slab = existing_slab
                        created = False
                    else:
                        slab, created = SpSlab.objects.get_or_create(
                            slab_no=slab_no,
                            defaults={
                                'horizon': row['horizon'] if pd.notna(row['horizon']) else None,
                                'counterpart': row.get('Counterpart?', '') if pd.notna(row.get('Counterpart?')) else ''
                            }
                        )
                    
                    if created:
                        created_slabs += 1
                        self.stdout.write(self.style.SUCCESS(f'Created new slab: {slab.slab_no}'))
                    
                    # Generate specimen number if not provided
                    if pd.isna(row.get('specimen no.')):
                        specimen_counters[slab_no] += 1
                        specimen_no = f"{slab_no}-{specimen_counters[slab_no]}"
                    else:
                        specimen_no = f"{slab_no}-{row['specimen no.']}"
                    
                    # Check if specimen exists
                    if options['skip_existing']:
                        try:
                            existing_specimen = SpFossilSpecimen.objects.get(specimen_no=specimen_no)
                            skipped_specimens += 1
                            specimens_dict[specimen_no] = existing_specimen
                            self.stdout.write(self.style.WARNING(
                                f'Skipping existing specimen: {specimen_no}'
                            ))
                            continue
                        except SpFossilSpecimen.DoesNotExist:
                            pass
                    
                    # Create the specimen
                    specimen = SpFossilSpecimen.objects.create(
                        slab=slab,
                        specimen_no=specimen_no,
                        taxon_name=row['taxon name'] if pd.notna(row['taxon name']) else None,
                        phylum=row['phylum'] if pd.notna(row['phylum']) else None,
                        remarks=row['remarks'] if pd.notna(row['remarks']) else None,
                        counterpart=row.get('Counterpart?', '') if pd.notna(row.get('Counterpart?')) else ''
                    )
                    
                    created_specimens += 1
                    # Store specimen for photo processing
                    specimens_dict[specimen_no] = specimen
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created specimen: {specimen.specimen_no} ({specimen.taxon_name or "No taxon"})'
                    ))
                
                # Process photos after all specimens are created
                photo_count = self.process_specimen_photos(base_path, specimens_dict, prefix, year)
                
                # Print statistics
                if options['skip_existing']:
                    self.stdout.write(self.style.SUCCESS(
                        f'Statistics (incremental update mode):\n'
                        f'  - Created slabs: {created_slabs}\n'
                        f'  - Skipped existing slabs: {skipped_slabs}\n'
                        f'  - Created specimens: {created_specimens}\n'
                        f'  - Skipped existing specimens: {skipped_specimens}\n'
                        f'  - Processed photos: {photo_count}'
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'Statistics (replacement mode):\n'
                        f'  - Created slabs: {created_slabs}\n'
                        f'  - Created specimens: {created_specimens}\n'
                        f'  - Processed photos: {photo_count}'
                    ))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))
            raise e

        self.stdout.write(self.style.SUCCESS('Successfully imported all specimens and photos')) 