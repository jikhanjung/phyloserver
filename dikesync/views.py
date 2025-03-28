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
    """Submit a dike record with sync event"""
    sync_event = None
    try:
        logger.info("Received dike record submission request")
        logger.debug(f"Request data: {request.data}")
        
        event_id = request.data.get('event_id')
        if not event_id:
            logger.error("No event_id provided in request")
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Looking up sync event with ID: {event_id}")
        sync_event = get_object_or_404(SyncEvent, event_id=event_id)
        
        if sync_event.status == 'completed':
            logger.warning(f"Sync event {event_id} is already completed")
            return Response(
                {'error': 'Sync event is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update sync event status
        logger.info(f"Updating sync event {event_id} status to in_progress")
        sync_event.status = 'in_progress'
        sync_event.save()

        # Create dike record and sync event record
        dike_record_data = request.data.get('dike_record')
        if not dike_record_data:
            logger.error("No dike_record data provided in request")
            return Response(
                {'error': 'dike_record data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Creating dike record and sync event record")
        serializer = SyncEventRecordSerializer(data={
            'sync_event': sync_event.id,
            'dike_record': dike_record_data,
            'sync_result': 'success'
        })

        if serializer.is_valid():
            logger.info("Serializer validation successful")
            logger.debug(f"Validated data: {serializer.validated_data}")
            serializer.save()
            logger.info("Successfully saved dike record and sync event record")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.error(f"Serializer validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error in submit_dike_record: {str(e)}")
        logger.error(traceback.format_exc())
        if sync_event:
            logger.info(f"Updating sync event {sync_event.event_id} status to failed")
            sync_event.status = 'failed'
            sync_event.error_message = str(e)
            sync_event.save()
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
    """Submit multiple dike records with sync event"""
    sync_event = None
    try:
        logger.info("Received multiple dike records submission request")
        logger.debug(f"Request data: {request.data}")
        
        event_id = request.data.get('event_id')
        if not event_id:
            logger.error("No event_id provided in request")
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Looking up sync event with ID: {event_id}")
        sync_event = get_object_or_404(SyncEvent, event_id=event_id)
        
        if sync_event.status == 'completed':
            logger.warning(f"Sync event {event_id} is already completed")
            return Response(
                {'error': 'Sync event is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update sync event status
        logger.info(f"Updating sync event {event_id} status to in_progress")
        sync_event.status = 'in_progress'
        sync_event.save()

        # Get list of dike records
        dike_records = request.data.get('dike_records', [])
        if not dike_records:
            logger.error("No dike_records provided in request")
            return Response(
                {'error': 'dike_records list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Processing {len(dike_records)} dike records")
        results = []
        errors = []

        with transaction.atomic():
            for index, dike_record_data in enumerate(dike_records):
                try:
                    logger.debug(f"Processing dike record {index + 1}/{len(dike_records)}")
                    serializer = SyncEventRecordSerializer(data={
                        'sync_event': sync_event.id,
                        'dike_record': dike_record_data,
                        'sync_result': 'success'
                    })

                    if serializer.is_valid():
                        serializer.save()
                        results.append({
                            'index': index,
                            'status': 'success',
                            'data': serializer.data
                        })
                    else:
                        errors.append({
                            'index': index,
                            'status': 'error',
                            'errors': serializer.errors
                        })
                        logger.error(f"Validation error for record {index}: {serializer.errors}")
                except Exception as e:
                    errors.append({
                        'index': index,
                        'status': 'error',
                        'error': str(e)
                    })
                    logger.error(f"Error processing record {index}: {str(e)}")
                    logger.error(traceback.format_exc())

        # Update sync event status based on results
        if errors:
            sync_event.status = 'failed'
            sync_event.error_message = f"Failed to process {len(errors)} records"
            sync_event.save()
        else:
            sync_event.status = 'completed'
            sync_event.save()

        return Response({
            'success_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in submit_dike_records: {str(e)}")
        logger.error(traceback.format_exc())
        if sync_event:
            logger.info(f"Updating sync event {sync_event.event_id} status to failed")
            sync_event.status = 'failed'
            sync_event.error_message = str(e)
            sync_event.save()
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
