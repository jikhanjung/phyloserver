from rest_framework import serializers
from .models import DikeRecord, SyncEvent
import logging

logger = logging.getLogger(__name__)

class DikeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DikeRecord
        fields = '__all__'

class SyncEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncEvent
        fields = '__all__'

    def create(self, validated_data):
        logger.debug(f"Creating SyncEvent with validated_data: {validated_data}")
        
        sync_event = SyncEvent.objects.create(**validated_data)
        logger.debug(f"Created SyncEvent with ID: {sync_event.id}")
        
        return sync_event 