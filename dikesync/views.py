from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import DikeRecord, SyncEvent, SyncEventRecord
from .serializers import DikeRecordSerializer, SyncEventSerializer, SyncEventRecordSerializer
import logging
import traceback
from django.db import transaction

# Set up logging
logger = logging.getLogger(__name__)

# Create your views here.

class SyncEventViewSet(viewsets.ModelViewSet):
    queryset = SyncEvent.objects.all()
    serializer_class = SyncEventSerializer
    lookup_field = 'event_id'
    lookup_url_kwarg = 'event_id'

    @action(detail=False, methods=['post'])
    def create_new(self, request):
        """Create a new sync event and return its ID"""
        try:
            logger.info("Creating new sync event")
            sync_event = SyncEvent.create_new_event()
            serializer = self.get_serializer(sync_event)
            logger.info(f"Successfully created sync event with ID: {sync_event.event_id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error creating sync event: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def end_sync(self, request, event_id=None):
        """End a sync event and mark it as completed"""
        try:
            logger.info(f"Ending sync event with ID: {event_id}")
            sync_event = self.get_object()
            
            if sync_event.status == 'completed':
                logger.warning(f"Sync event {event_id} is already completed")
                return Response(
                    {'error': 'Sync event is already completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if sync_event.status == 'failed':
                logger.warning(f"Sync event {event_id} has failed and cannot be completed")
                return Response(
                    {'error': 'Failed sync events cannot be completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            sync_event.status = 'completed'
            sync_event.save()
            
            logger.info(f"Successfully ended sync event {event_id}")
            serializer = self.get_serializer(sync_event)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error ending sync event: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DikeRecordViewSet(viewsets.ModelViewSet):
    queryset = DikeRecord.objects.all()
    serializer_class = DikeRecordSerializer

@api_view(['POST'])
def submit_dike_record(request):
    """Submit a single dike record with sync event ID"""
    try:
        logger.info("Received dike record submission request")
        logger.info(f"Request data: {request.data}")
        
        # Get sync event ID from request
        event_id = request.data.get('event_id')
        if not event_id:
            logger.error("No event_id provided in request")
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get sync event
        try:
            sync_event = get_object_or_404(SyncEvent, event_id=event_id)
        except (SyncEvent.DoesNotExist, ValueError) as e:
            logger.error(f"Invalid sync event ID: {event_id}")
            return Response(
                {'error': 'Invalid sync event ID'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if event is already completed
        if sync_event.status == 'completed':
            logger.warning(f"Sync event {event_id} is already completed")
            return Response(
                {'error': 'Sync event is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update event status to in_progress
        sync_event.status = 'in_progress'
        sync_event.save()
        
        # Validate specimen form
        specimen_data = request.data.get('dike_record', {})
        if not specimen_data:
            logger.error("No dike record data provided")
            return Response(
                {'error': 'dike_record data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for unique_id and existing record
        unique_id = specimen_data.get('unique_id')
        if unique_id:
            try:
                existing_record = DikeRecord.objects.get(unique_id=unique_id)
                logger.info(f"Found existing record with unique_id: {unique_id}")
                # Update existing record
                for key, value in specimen_data.items():
                    setattr(existing_record, key, value)
                existing_record.save()
                dike_record = existing_record
            except DikeRecord.DoesNotExist:
                logger.info(f"No existing record found with unique_id: {unique_id}")
                dike_record = DikeRecord.objects.create(**specimen_data)
        else:
            logger.info("No unique_id provided, creating new record")
            dike_record = DikeRecord.objects.create(**specimen_data)
        
        # Create sync event record
        sync_record = SyncEventRecord.objects.create(
            sync_event=sync_event,
            dike_record=dike_record,
            sync_result='success'
        )
        
        logger.info(f"Successfully processed dike record with ID: {dike_record.id}")
        return Response({
            'message': 'Dike record processed successfully',
            'dike_record_id': dike_record.id,
            'unique_id': dike_record.unique_id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing dike record: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def check_sync_status(request, event_id):
    """Check the status of a sync event"""
    try:
        logger.info(f"Checking sync status for event_id: {event_id}")
        sync_event = get_object_or_404(SyncEvent, event_id=event_id)
        serializer = SyncEventSerializer(sync_event)
        logger.info(f"Sync event {event_id} status: {sync_event.status}")
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error checking sync status: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def submit_dike_records(request):
    """Submit multiple dike records with sync event ID"""
    try:
        logger.info("Received multiple dike records submission request")
        logger.info(f"Request data: {request.data}")
        
        # Get sync event ID from request
        event_id = request.data.get('event_id')
        if not event_id:
            logger.error("No event_id provided in request")
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get sync event
        try:
            sync_event = get_object_or_404(SyncEvent, event_id=event_id)
        except (SyncEvent.DoesNotExist, ValueError) as e:
            logger.error(f"Invalid sync event ID: {event_id}")
            return Response(
                {'error': 'Invalid sync event ID'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if event is already completed
        if sync_event.status == 'completed':
            logger.warning(f"Sync event {event_id} is already completed")
            return Response(
                {'error': 'Sync event is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update event status to in_progress
        sync_event.status = 'in_progress'
        sync_event.save()
        
        # Get list of dike records
        dike_records = request.data.get('dike_records', [])
        if not dike_records:
            logger.error("No dike records provided")
            return Response(
                {'error': 'dike_records list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success_count = 0
        error_count = 0
        results = []
        errors = []
        
        # Process each record in a transaction
        with transaction.atomic():
            for index, record_data in enumerate(dike_records):
                try:
                    # Check for unique_id and existing record
                    unique_id = record_data.get('unique_id')
                    if unique_id:
                        try:
                            existing_record = DikeRecord.objects.get(unique_id=unique_id)
                            logger.info(f"Found existing record with unique_id: {unique_id}")
                            # Update existing record
                            for key, value in record_data.items():
                                setattr(existing_record, key, value)
                            existing_record.save()
                            dike_record = existing_record
                        except DikeRecord.DoesNotExist:
                            logger.info(f"No existing record found with unique_id: {unique_id}")
                            dike_record = DikeRecord.objects.create(**record_data)
                    else:
                        logger.info("No unique_id provided, creating new record")
                        dike_record = DikeRecord.objects.create(**record_data)
                    
                    # Create sync event record
                    sync_record = SyncEventRecord.objects.create(
                        sync_event=sync_event,
                        dike_record=dike_record,
                        sync_result='success'
                    )
                    
                    success_count += 1
                    results.append({
                        'index': index,
                        'status': 'success',
                        'data': {
                            'dike_record_id': dike_record.id,
                            'unique_id': dike_record.unique_id
                        }
                    })
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing record at index {index}: {str(e)}")
                    errors.append({
                        'index': index,
                        'status': 'error',
                        'errors': str(e)
                    })
        
        # Update sync event status based on results
        if error_count == 0:
            sync_event.status = 'completed'
        else:
            sync_event.status = 'failed'
            sync_event.error_message = f"Failed to process {error_count} records"
        sync_event.save()
        
        return Response({
            'success_count': success_count,
            'error_count': error_count,
            'results': results,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error processing dike records: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def sync_event_list(request):
    """Display list of all sync events"""
    sync_events = SyncEvent.objects.all().order_by('-timestamp')
    return render(request, 'dikesync/sync_event_list.html', {
        'sync_events': sync_events
    })

def sync_event_detail(request, event_id):
    """Display details of a sync event and its dike records"""
    sync_event = get_object_or_404(SyncEvent, event_id=event_id)
    sync_records = SyncEventRecord.objects.filter(sync_event=sync_event).order_by('-timestamp')
    return render(request, 'dikesync/sync_event_detail.html', {
        'sync_event': sync_event,
        'sync_records': sync_records
    })
