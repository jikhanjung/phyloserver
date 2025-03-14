from django.db import models
import os, re
from django.utils.timezone import now

def fossil_image_upload_path(instance, filename):
    """
    표본 발견 연도 기반 디렉토리 구조로 이미지를 저장.
    - 표본번호가 SP-2017-1-001이라면, 2017/ 디렉토리 아래 저장
    - 파일명은 specimen_no_순번.확장자로 저장
    """
    # 표본번호에서 연도를 추출 (SP-YYYY 패턴)
    match = re.match(r"(\w+)-(20\d{2})", instance.specimen.specimen_no)
    prefix = match.group(1) if match else "unknown"
    year = match.group(2) if match else "unknown"

    # 원본 파일 확장자 유지
    ext = filename.split('.')[-1]

    # 파일명: specimen_no_파일명.확장자
    specimen_id = instance.specimen.specimen_no
    file_basename = f"{specimen_id}_{instance.pk or 'temp'}.{ext}"

    return os.path.join(f"photos/{prefix}/{year}/", file_basename)

# Create your models here.
class SpSlab(models.Model):
    """
    슬랩(Slab) 정보를 관리하는 모델.
    여러 표본(FossilSample)이 붙어 있을 수 있는 암석조각 단위.
    """
    slab_no = models.CharField( '슬랩 번호', max_length=100, unique=True, db_index=True, help_text='고유 슬랩 식별 번호 (예: SLAB-01)')
    counterpart = models.CharField( '대응 슬랩', max_length=100, default=False )
    horizon = models.CharField( '층준', max_length=100, blank=True, null=True,  help_text='이 슬랩이 발견된 층준 정보')
    expedition_year = models.CharField( '탐사연도', max_length=4, blank=True, null=True,  help_text='이 슬랩이 발견된 탐사 연도')
    location = models.CharField( '보관 위치', max_length=100, blank=True, null=True, help_text='슬랩이 보관된 위치(수장고 정보 등)' )
    created_on = models.DateTimeField( '등록 시각', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    modified_on = models.DateTimeField( '마지막 수정 시각', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)

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
    specimen_no = models.CharField( '표본 번호', max_length=100, db_index=True, help_text='개별 표본 식별 번호 (예: SP-2017-1-001)' )
    taxon_name = models.CharField( '학명', max_length=100, blank=True, null=True )
    phylum = models.CharField( '문(Phylum)', max_length=100, blank=True, null=True )
    remarks = models.TextField( '비고', blank=True, null=True )
    counterpart = models.CharField( '대응 표본', max_length=100, default=False )
    created_on = models.DateTimeField( '등록 시각', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    modified_on = models.DateTimeField( '마지막 수정 시각', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)

    class Meta:
        # 슬랩-샘플번호 조합이 고유해야 한다면 unique_together 적용
        unique_together = ('slab', 'specimen_no')
        ordering = ['slab', 'specimen_no']
        verbose_name = '화석 표본'
        verbose_name_plural = '화석 표본 목록'

    def __str__(self):
        return f'[Slab: {self.slab.slab_no}] Specimen: {self.specimen_no} ({self.taxon_name})'
    
class SpFossilSpecimenImage(models.Model):
    """
    FossilSpecimen(화석 표본)과 연결된 이미지 정보를 관리하는 모델.
    하나의 표본에 여러 장의 사진이 연결될 수 있다.
    """
    specimen = models.ForeignKey( SpFossilSpecimen, on_delete=models.CASCADE, related_name='images', help_text="이 이미지가 속한 화석 표본" )
    image_file = models.ImageField( upload_to=fossil_image_upload_path, help_text="표본 사진 파일" )
    description = models.TextField( "설명", blank=True, null=True, help_text="사진에 대한 설명 (예: 촬영 각도, 확대 배율 등)" )
    created_on = models.DateTimeField( '등록 시각', auto_now_add=True )
    created_by = models.CharField(max_length=50,blank=True)
    modified_on = models.DateTimeField( '마지막 수정 시각', auto_now=True )
    modified_by = models.CharField(max_length=50,blank=True)

    class Meta:
        ordering = ['specimen', 'created_on']
        verbose_name = "화석 표본 사진"
        verbose_name_plural = "화석 표본 사진 목록"

    def __str__(self):
        return f"[Specimen: {self.specimen.specimen_no}] Image: {self.image_file.name}"