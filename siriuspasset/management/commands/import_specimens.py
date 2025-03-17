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

class Command(BaseCommand):
    help = 'Import specimens data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument('--no-delete', action='store_true', help='Skip deletion of existing records')

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

    def process_specimen_photos(self, base_path, specimens):
        """
        Process specimen photos in the directory structure.
        base_path: directory containing the Excel file and photo directories
        specimens: dict of specimens keyed by specimen_no for quick lookup
        """
        # Print debug information about available specimens
        self.stdout.write(self.style.WARNING(f"Available specimen numbers: {list(specimens.keys())}"))
        
        # Pattern for filenames like:
        # "SP-2016-1A-1.JPG" or "SP-2016-1-1.JPG" (non-padded numbers)
        specimen_pattern = re.compile(r'(SP-\d{4})-(\d+)([A-Z]?)-(\d+)\.[Jj][Pp][Gg]')
        
        base_path = Path(base_path)
        photo_count = 0
        media_root = Path(settings.MEDIA_ROOT)

        # Debug: Print the base path being searched
        self.stdout.write(self.style.WARNING(f"Searching for photos in: {base_path}"))

        # Walk through all subdirectories
        for root, dirs, files in os.walk(base_path):
            # Debug: Print current directory being processed
            self.stdout.write(self.style.WARNING(f"Checking directory: {root}"))
            self.stdout.write(self.style.WARNING(f"Found files: {[f for f in files if f.lower().endswith('.jpg')]}"))
            
            for filename in files:
                if filename.lower().endswith('.jpg'):
                    file_path = Path(root) / filename
                    
                    # Debug: Print file being processed
                    self.stdout.write(self.style.WARNING(f"Processing file: {filename}"))
                    
                    # Try matching the filename pattern
                    match = specimen_pattern.match(filename)
                    if match:
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
                                # Create and save the image instance first to get a primary key
                                image = SpFossilSpecimenImage.objects.create(
                                    specimen=specimen,
                                    description=f"Photo sequence {sequence}"
                                )
                                
                                # Now that we have a primary key, manually construct the path
                                # Extract year from specimen number (SP-YYYY pattern)
                                match_year = re.match(r"(\w+)-(20\d{2})", specimen.specimen_no)
                                prefix = match_year.group(1) if match_year else "unknown"
                                year = match_year.group(2) if match_year else "unknown"
                                
                                # Keep original filename
                                ext = filename.split('.')[-1]
                                target_filename = filename
                                
                                # Create target directory if it doesn't exist
                                target_dir = os.path.join(settings.MEDIA_ROOT, f"photos/{prefix}/{year}/")
                                os.makedirs(target_dir, exist_ok=True)
                                
                                # Copy the file to the target location
                                target_path = os.path.join(target_dir, target_filename)
                                shutil.copy2(file_path, target_path)
                                
                                # Update the image_file field with the relative path
                                relative_path = os.path.join(f"photos/{prefix}/{year}/", target_filename)
                                image.image_file = relative_path
                                image.save()

                                photo_count += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f'Added photo {filename} to specimen {specimen_id} at {relative_path}'
                                ))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(
                                    f'Error processing photo {filename}: {str(e)}'
                                ))
                        else:
                            self.stdout.write(self.style.WARNING(
                                f'No matching specimen found for photo {filename} (ID: {specimen_id})'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"File {filename} did not match the expected pattern"
                        ))

        return photo_count

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        base_path = os.path.dirname(os.path.abspath(excel_file))
        
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
                # Delete existing records if --no-delete is not specified
                if not options['no_delete']:
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
                
                # Process each row in the dataframe
                for _, row in df.iterrows():
                    original_slab_no = row['slab no.']
                    # Format the slab number with 4 digits
                    slab_no = self.format_slab_number(original_slab_no, prefix, year)
                    
                    if slab_no != original_slab_no:
                        self.stdout.write(self.style.SUCCESS(
                            f'Formatted slab number: {original_slab_no} -> {slab_no}'
                        ))
                    
                    # Get or create the slab
                    slab, created = SpSlab.objects.get_or_create(
                        slab_no=slab_no,
                        defaults={
                            'horizon': row['horizon'] if pd.notna(row['horizon']) else None,
                            'counterpart': row.get('Counterpart?', '') if pd.notna(row.get('Counterpart?')) else ''
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created new slab: {slab.slab_no}'))
                    
                    # Generate specimen number if not provided
                    if pd.isna(row.get('specimen no.')):
                        specimen_counters[slab_no] += 1
                        specimen_no = f"{slab_no}-{specimen_counters[slab_no]}"
                    else:
                        specimen_no = f"{slab_no}-{row['specimen no.']}"
                    
                    # Create the specimen
                    specimen = SpFossilSpecimen.objects.create(
                        slab=slab,
                        specimen_no=specimen_no,
                        taxon_name=row['taxon name'] if pd.notna(row['taxon name']) else None,
                        phylum=row['phylum'] if pd.notna(row['phylum']) else None,
                        remarks=row['remarks'] if pd.notna(row['remarks']) else None,
                        counterpart=row.get('Counterpart?', '') if pd.notna(row.get('Counterpart?')) else ''
                    )
                    
                    # Store specimen for photo processing
                    specimens_dict[specimen_no] = specimen
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created specimen: {specimen.specimen_no} ({specimen.taxon_name or "No taxon"})'
                    ))
                
                # Process photos after all specimens are created
                photo_count = self.process_specimen_photos(base_path, specimens_dict)
                self.stdout.write(self.style.SUCCESS(f'Processed {photo_count} specimen photos'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))
            raise e

        self.stdout.write(self.style.SUCCESS('Successfully imported all specimens and photos')) 