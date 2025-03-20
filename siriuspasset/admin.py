from django.contrib import admin
from siriuspasset.models import (
    SpSlab, SpFossilSpecimen, SpFossilImage, 
    DirectoryScan, SpImageProcessingRecord
)

# Register your models here.

@admin.register(SpImageProcessingRecord)
class SpImageProcessingRecordAdmin(admin.ModelAdmin):
    list_display = ('filename', 'status', 'process_datetime', 'command_used')
    list_filter = ('status', 'command_used', 'process_datetime')
    search_fields = ('filename', 'original_path', 'status_message')
    readonly_fields = ('process_datetime',)
    date_hierarchy = 'process_datetime'
    
    fieldsets = (
        (None, {
            'fields': ('filename', 'original_path', 'md5hash')
        }),
        ('Processing Status', {
            'fields': ('status', 'status_message', 'command_used', 'process_datetime')
        }),
        ('Related Records', {
            'fields': ('image', 'slab', 'specimen')
        }),
    )
