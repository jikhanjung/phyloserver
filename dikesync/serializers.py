from rest_framework import serializers
from .models import DikeRecord, SyncEvent, SyncEventRecord
import logging

logger = logging.getLogger(__name__)

class DikeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DikeRecord
        fields = ['id', 'unique_id', 'symbol', 'stratum', 'rock_type', 'era', 'map_sheet', 
                 'address', 'distance', 'angle', 'x_coord_1', 'y_coord_1', 'lat_1', 'lng_1',
                 'x_coord_2', 'y_coord_2', 'lat_2', 'lng_2', 'memo', 'created_date', 'modified_date']
        read_only_fields = ['unique_id', 'created_date', 'modified_date']

class SyncEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncEvent
        fields = '__all__'
        read_only_fields = ('timestamp',)

class SyncEventRecordSerializer(serializers.ModelSerializer):
    dike_record = DikeRecordSerializer()
    sync_event = serializers.PrimaryKeyRelatedField(queryset=SyncEvent.objects.all())

    class Meta:
        model = SyncEventRecord
        fields = '__all__'
        read_only_fields = ('timestamp',)

    def create(self, validated_data):
        logger.debug(f"Creating SyncEventRecord with validated_data: {validated_data}")
        
        dike_record_data = validated_data.pop('dike_record')
        sync_event = validated_data.pop('sync_event')
        
        logger.debug(f"Creating DikeRecord with data: {dike_record_data}")
        dike_record = DikeRecord.objects.create(**dike_record_data)
        logger.debug(f"Created DikeRecord with ID: {dike_record.id}")
        
        logger.debug(f"Creating SyncEventRecord with sync_event: {sync_event}")
        sync_event_record = SyncEventRecord.objects.create(
            dike_record=dike_record,
            sync_event=sync_event,
            sync_result=validated_data.get('sync_result', 'success')
        )
        logger.debug(f"Created SyncEventRecord with ID: {sync_event_record.id}")
        
        return sync_event_record 