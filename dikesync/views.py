from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import DikeRecord, SyncEvent
from .serializers import DikeRecordSerializer, SyncEventSerializer
import logging
import traceback
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.contrib import messages

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
            sync_event.end_timestamp = timezone.now()
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

def dike_record_detail(request, record_id):
    """Display details of an individual dike record"""
    dike_record = get_object_or_404(DikeRecord, id=record_id)
    # Get the most recent sync event for this record
    sync_event = SyncEvent.objects.filter(
        timestamp__lte=dike_record.last_sync_date
    ).order_by('-timestamp').first()
    
    return render(request, 'dikesync/dike_record_detail.html', {
        'dike_record': dike_record,
        'sync_event': sync_event
    })

def dike_record_edit(request, record_id):
    """Edit an individual dike record"""
    dike_record = get_object_or_404(DikeRecord, id=record_id)
    
    if request.method == 'POST':
        try:
            logger.info(f"Received POST request to edit dike record {record_id}")
            logger.info(f"Current record data: unique_id={dike_record.unique_id}, symbol={dike_record.symbol}")
            logger.info(f"Form data received: {request.POST}")
            
            # Update the record with form data
            new_unique_id = request.POST.get('unique_id')
            new_symbol = request.POST.get('symbol')
            new_stratum = request.POST.get('stratum')
            new_memo = request.POST.get('memo')
            
            logger.info(f"New values to be set: unique_id={new_unique_id}, symbol={new_symbol}")
            
            # Check if values are different before updating
            if dike_record.unique_id != new_unique_id:
                logger.info(f"Updating unique_id from {dike_record.unique_id} to {new_unique_id}")
            if dike_record.symbol != new_symbol:
                logger.info(f"Updating symbol from {dike_record.symbol} to {new_symbol}")
            if dike_record.stratum != new_stratum:
                logger.info(f"Updating stratum from {dike_record.stratum} to {new_stratum}")
            if dike_record.memo != new_memo:
                logger.info(f"Updating memo from {dike_record.memo} to {new_memo}")
            
            # Update the record
            dike_record.unique_id = new_unique_id
            dike_record.symbol = new_symbol
            dike_record.stratum = new_stratum
            dike_record.memo = new_memo
            
            # Save the record
            logger.info("Attempting to save the record...")
            dike_record.save()
            logger.info("Record saved successfully")
            
            # Verify the save
            saved_record = DikeRecord.objects.get(id=record_id)
            logger.info(f"Verified saved record data: unique_id={saved_record.unique_id}, symbol={saved_record.symbol}")
            
            messages.success(request, 'Dike record updated successfully.')
            return redirect('dike-record-detail', record_id=dike_record.id)
        except Exception as e:
            logger.error(f"Error updating dike record: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(request, f'Error updating dike record: {str(e)}')
    
    return render(request, 'dikesync/dike_record_edit.html', {
        'dike_record': dike_record
    })

@api_view(['GET'])
def get_changed_records(request):
    """Get records that changed after a specific sync event or datetime"""
    try:
        logger.info("Received request for changed records")
        logger.info(f"Request data: {request.data}")
        
        # Get either event_id or datetime from request
        event_id = request.data.get('event_id')
        datetime_str = request.data.get('datetime')
        
        if not event_id and not datetime_str:
            logger.error("Neither event_id nor datetime provided")
            return Response(
                {'error': 'Either event_id or datetime is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event_id and datetime_str:
            logger.error("Both event_id and datetime provided")
            return Response(
                {'error': 'Provide either event_id or datetime, not both'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Base queryset
        queryset = DikeRecord.objects.all()
        
        if event_id:
            # Get records changed after the sync event
            try:
                sync_event = get_object_or_404(SyncEvent, event_id=event_id)
                if sync_event.status != 'completed':
                    logger.warning(f"Sync event {event_id} is not completed")
                    return Response(
                        {'error': 'Sync event must be completed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(last_sync_date__gt=sync_event.end_timestamp)
                logger.info(f"Filtering records changed after sync event {event_id}")
            except (SyncEvent.DoesNotExist, ValueError) as e:
                logger.error(f"Invalid sync event ID: {event_id}")
                return Response(
                    {'error': 'Invalid sync event ID'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get records changed after the specified datetime
            try:
                datetime_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                queryset = queryset.filter(last_sync_date__gt=datetime_obj)
                logger.info(f"Filtering records changed after datetime {datetime_str}")
            except ValueError as e:
                logger.error(f"Invalid datetime format: {datetime_str}")
                return Response(
                    {'error': 'Invalid datetime format. Use ISO format (e.g., 2024-03-20T10:00:00Z)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get the records
        records = queryset.order_by('-last_sync_date')
        
        # Serialize the records
        serializer = DikeRecordSerializer(records, many=True)
        
        return Response({
            'count': len(records),
            'records': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error getting changed records: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
                existing_record.last_sync_date = timezone.now()
                existing_record.save()
                dike_record = existing_record
            except DikeRecord.DoesNotExist:
                logger.info(f"No existing record found with unique_id: {unique_id}")
                specimen_data['last_sync_date'] = timezone.now()
                dike_record = DikeRecord.objects.create(**specimen_data)
        else:
            logger.info("No unique_id provided, creating new record")
            specimen_data['last_sync_date'] = timezone.now()
            dike_record = DikeRecord.objects.create(**specimen_data)
        
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
                            existing_record.last_sync_date = timezone.now()
                            existing_record.save()
                            dike_record = existing_record
                        except DikeRecord.DoesNotExist:
                            logger.info(f"No existing record found with unique_id: {unique_id}")
                            record_data['last_sync_date'] = timezone.now()
                            dike_record = DikeRecord.objects.create(**record_data)
                    else:
                        logger.info("No unique_id provided, creating new record")
                        record_data['last_sync_date'] = timezone.now()
                        dike_record = DikeRecord.objects.create(**record_data)
                    
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
            sync_event.end_timestamp = timezone.now()
        else:
            sync_event.status = 'failed'
            sync_event.error_message = f"Failed to process {error_count} records"
            sync_event.end_timestamp = timezone.now()
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
    dike_records = DikeRecord.objects.filter(last_sync_date__gte=sync_event.timestamp).order_by('-last_sync_date')
    return render(request, 'dikesync/sync_event_detail.html', {
        'sync_event': sync_event,
        'dike_records': dike_records
    })
