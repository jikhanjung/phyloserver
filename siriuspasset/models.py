from django.db import models
import os, re
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image as PILImage
from django.utils import timezone

# Configuration for image directory structure
# Number of slabs per directory (e.g., 100 gives 0001-0100, 1000 gives 0001-1000)
SLABS_PER_DIRECTORY = 100

# Thumbnail size for gallery view (width, height)
THUMBNAIL_SIZE = (300, 300)

def fossil_image_upload_path(instance, filename):
    """
    표본 발견 연도 및 슬랩 번호 범위 기반 디렉토리 구조로 이미지를 저장.
    - 표본번호가 SP-2017-0042-001이라면, SP/2017/0001-0100/ 디렉토리 아래 저장
    - 슬랩번호가 SP-2017-0142라면, SP/2017/0101-0200/ 디렉토리 아래 저장
    - 파일명은 specimen_no_순번.확장자로 저장
    """
    # 표본번호에서 연도와 슬랩 번호를 추출
    if instance.specimen:
        ref_obj = instance.specimen
        specimen_id = ref_obj.specimen_no
    else:
        ref_obj = instance.slab
        specimen_id = ref_obj.slab_no
        
    match = re.match(r"(\w+)-(20\d{2})-(\d+)", specimen_id)
    
    if match:
        prefix = match.group(1)  # SP
        year = match.group(2)    # 2016, 2017, etc.
        slab_num = match.group(3)  # Extract the slab number
        
        # Convert slab number to an integer and calculate the range directory
        try:
            slab_num_int = int(slab_num)
            # Calculate the range bucket based on SLABS_PER_DIRECTORY
            range_start = ((slab_num_int - 1) // SLABS_PER_DIRECTORY) * SLABS_PER_DIRECTORY + 1
            range_end = range_start + SLABS_PER_DIRECTORY - 1
            range_dir = f"{range_start:04d}-{range_end:04d}"
        except ValueError:
            # If conversion fails, use a default directory
            range_dir = "other"
    else:
        # Fallback if the pattern doesn't match
        prefix = "unknown"
        year = "unknown"
        range_dir = "unknown"

    # 원본 파일 확장자 유지
    ext = filename.split('.')[-1]

    # 파일명: specimen_no_파일명.확장자
    file_basename = f"{specimen_id}_{instance.pk or 'temp'}.{ext}"

    return os.path.join(f"sp_photos/{prefix}/{year}/{range_dir}/", file_basename)

# Create your models here.
class SpSlab(models.Model):
    """
    슬랩(Slab) 정보를 관리하는 모델.
    여러 표본(FossilSample)이 붙어 있을 수 있는 암석조각 단위.
    """
    slab_no = models.CharField( 'Slab no.', max_length=100, unique=True, db_index=True, help_text='고유 슬랩 식별 번호 (예: SLAB-01)')
    counterpart = models.CharField( 'Counterpart', max_length=100, null=True, blank=True )
    horizon = models.CharField( 'Horizon', max_length=100, blank=True, null=True,  help_text='이 슬랩이 발견된 층준 정보')
    expedition_year = models.CharField( 'Year', max_length=4, blank=True, null=True,  help_text='이 슬랩이 발견된 탐사 연도')
    location = models.CharField( 'Location', max_length=100, blank=True, null=True, help_text='슬랩이 보관된 위치(수장고 정보 등)' )
    created_on = models.DateTimeField( 'Created on', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    created_ip = models.GenericIPAddressField('Created IP', blank=True, null=True, help_text='IP address of the user who created this record')
    modified_on = models.DateTimeField( 'Modified on', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)
    modified_ip = models.GenericIPAddressField('Modified IP', blank=True, null=True, help_text='IP address of the user who last modified this record')

    class Meta:
        ordering = ['slab_no']
        verbose_name = '슬랩'
        verbose_name_plural = '슬랩 목록'

    def __str__(self):
        if self.horizon:
            return f'{self.slab_no} (Horizon: {self.horizon.name})'
        return f'{self.slab_no}'


class SpFossilSpecimen(models.Model):
    """
    슬랩 위의 표본(Specimen) 정보를 관리하는 모델.
    """
    slab = models.ForeignKey( SpSlab, on_delete=models.CASCADE, related_name='specimens', help_text='해당 표본이 속한 슬랩(예:SP-2017-1)' )
    specimen_no = models.CharField( 'Specimen number', max_length=100, db_index=True, help_text='개별 표본 식별 번호 (예: SP-2017-1-001)' )
    taxon_name = models.CharField( 'Taxon name', max_length=100, blank=True, null=True )
    phylum = models.CharField( 'Phylum', max_length=100, blank=True, null=True )
    remarks = models.TextField( 'Remarks', blank=True, null=True )
    counterpart = models.CharField( 'Counterpart', max_length=100, null=True, blank=True )
    created_on = models.DateTimeField( 'Created on', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    created_ip = models.GenericIPAddressField('Created IP', blank=True, null=True, help_text='IP address of the user who created this record')
    modified_on = models.DateTimeField( 'Modified on', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)
    modified_ip = models.GenericIPAddressField('Modified IP', blank=True, null=True, help_text='IP address of the user who last modified this record')

    class Meta:
        # 슬랩-샘플번호 조합이 고유해야 한다면 unique_together 적용
        unique_together = ('slab', 'specimen_no')
        ordering = ['slab', 'specimen_no']
        verbose_name = '화석 표본'
        verbose_name_plural = '화석 표본 목록'

    def __str__(self):
        return f'[Slab: {self.slab.slab_no}] Specimen: {self.specimen_no} ({self.taxon_name})'
    
class SpFossilImage(models.Model):
    """
    화석 사진을 관리하는 모델.
    슬랩이나 표본에 연결될 수 있으며, 둘 중 하나는 반드시 지정되어야 함.
    """
    slab = models.ForeignKey( SpSlab, on_delete=models.CASCADE, related_name='images', null=True, blank=True, help_text="이 이미지가 속한 슬랩" )
    specimen = models.ForeignKey( SpFossilSpecimen, on_delete=models.CASCADE, related_name='images', null=True, blank=True, help_text="이 이미지가 속한 화석 표본" )
    image_file = models.ImageField( upload_to=fossil_image_upload_path, help_text="화석 사진 파일" )
    description = models.TextField( "Description", blank=True, null=True, help_text="사진에 대한 설명 (예: 촬영 각도, 확대 배율 등)" )
    original_path = models.CharField( "Original path", max_length=500, blank=True, null=True, help_text="원본 이미지 파일의 경로" )
    md5hash = models.CharField( "MD5 hash", max_length=32, blank=True, null=True, help_text="이미지 파일의 MD5 해시값", db_index=True )
    created_on = models.DateTimeField( 'Created on', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    modified_on = models.DateTimeField( 'Modified on', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)

    class Meta:
        ordering = ['created_on']
        verbose_name = "Fossil image"
        verbose_name_plural = "Fossil images"
        # Add unique constraint for md5hash to prevent duplicates
        constraints = [
            models.UniqueConstraint(fields=['md5hash'], name='unique_image_hash', condition=models.Q(md5hash__isnull=False)),
            models.CheckConstraint(
                check=models.Q(slab__isnull=False) | models.Q(specimen__isnull=False),
                name='slab_or_specimen_not_null'
            )
        ]

    def __str__(self):
        if self.specimen:
            return f"[Specimen: {self.specimen.specimen_no}] Image: {self.image_file.name}"
        else:
            return f"[Slab: {self.slab.slab_no}] Image: {self.image_file.name}"

    def clean(self):
        """Validate that at least one of slab or specimen is set."""
        if not self.slab and not self.specimen:
            raise ValidationError("Either slab or specimen must be specified.")
    
    def get_thumbnail_path(self):
        """
        Returns the filesystem path for the thumbnail.
        """
        image_path = self.image_file.path
        image_dir = os.path.dirname(image_path)
        image_name = os.path.basename(image_path)
        
        thumbnail_dir = os.path.join(image_dir, '.thumbnails')
        thumbnail_path = os.path.join(thumbnail_dir, image_name)
        
        return thumbnail_path
    
    def generate_thumbnail(self):
        """
        Generate a thumbnail for this image file.
        Returns True if successful, False otherwise.
        """
        try:
            image_path = self.image_file.path
            thumbnail_path = self.get_thumbnail_path()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            # Open the image
            img = PILImage.open(image_path)
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # Create thumbnail
            img.thumbnail(THUMBNAIL_SIZE, PILImage.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, "JPEG", quality=90)
            return True
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
            return False
    
    def get_thumbnail_url(self):
        """
        Return the URL to the thumbnail image.
        If thumbnail doesn't exist, returns the original image URL.
        """
        thumbnail_path = self.get_thumbnail_path()
        
        # Check if thumbnail exists
        if os.path.exists(thumbnail_path):
            # Convert filesystem path to URL
            media_root = settings.MEDIA_ROOT
            relative_path = os.path.relpath(thumbnail_path, media_root)
            return f"{settings.MEDIA_URL}{relative_path.replace(os.sep, '/')}"
        else:
            # Return original image URL if thumbnail doesn't exist
            return self.image_file.url

class DirectoryScan(models.Model):
    """
    Records information about directory scans for new images,
    including when the scan was performed, what directory was scanned,
    and statistics about the import process.
    """
    scan_directory = models.CharField("Scanned Directory", max_length=255, help_text="Path of the scanned directory")
    scan_start_time = models.DateTimeField("Scan Start Time", auto_now_add=True, help_text="When the scan started")
    scan_end_time = models.DateTimeField("Scan End Time", null=True, blank=True, help_text="When the scan completed")
    scan_pattern = models.CharField("File Pattern", max_length=50, help_text="Pattern used to match files")
    total_files_found = models.IntegerField("Total Files Found", default=0, help_text="Total image files found")
    new_images_imported = models.IntegerField("New Images Imported", default=0, help_text="Number of new images imported")
    duplicate_images_skipped = models.IntegerField("Duplicate Images Skipped", default=0, help_text="Number of duplicate images skipped")
    existing_images_skipped = models.IntegerField("Existing Images Skipped", default=0, help_text="Number of existing images skipped")
    older_files_skipped = models.IntegerField("Older Files Skipped", default=0, help_text="Number of files skipped because they were created before the last scan")
    error_count = models.IntegerField("Errors Encountered", default=0, help_text="Number of errors encountered")
    status = models.CharField("Status", max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='in_progress')
    log_summary = models.TextField("Log Summary", blank=True, help_text="Summary of the scan log")
    
    # User who initiated the scan
    created_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-scan_start_time']
        verbose_name = 'Directory Scan'
        verbose_name_plural = 'Directory Scans'
    
    def __str__(self):
        return f"Scan of {self.scan_directory} on {self.scan_start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def duration(self):
        """Returns the duration of the scan in seconds, or None if not completed"""
        if self.scan_end_time:
            return (self.scan_end_time - self.scan_start_time).total_seconds()
        return None
    
    def mark_completed(self, status='completed'):
        """Mark this scan as completed with the given status"""
        self.status = status
        self.scan_end_time = timezone.now()
        self.save()