from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import SpFossilSpecimen, SpFossilImage, SpSlab, DirectoryScan
from django.core.paginator import Paginator
from .forms import SpFossilSpecimenForm, SpFossilImageForm, SpSlabForm
from django.urls import reverse
#from cStringIO import StringIO
from django.db.models import Q, Count
from django.db import transaction
from itertools import groupby
from operator import attrgetter
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.postgres.search import SearchVector
from siriuspasset.utils import sort_images_by_filename
import os
import time

# Helper function to get client IP address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list of IPs.
        # The client's IP will be the first one.
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Create your views here.
# Create your views here.
ITEMS_PER_PAGE = 20

def get_user_obj( request ):
    user_obj = request.user
    if str(user_obj) == 'AnonymousUser':
        return None
    #print("user_obj:", user_obj)
    user_obj.groupname_list = []
    for g in request.user.groups.all():
        user_obj.groupname_list.append(g.name)

    return user_obj


def index(request):
    return HttpResponseRedirect('specimen_list')

def show_table(request):
    return HttpResponseRedirect('specimen_list')


def specimen_list(request):
    user_obj = get_user_obj(request)

    # Get filter parameters
    filter1 = request.GET.get('filter1', '')
    filter2 = request.GET.get('filter2', '')
    page_no = int(request.GET.get('page', 1))

    # Query the specimens
    specimen_list = SpFossilSpecimen.objects.select_related('slab').all()

    # Apply filters if provided
    if filter1:
        specimen_list = specimen_list.filter(
            Q(specimen_no__icontains=filter1) |
            Q(taxon_name__icontains=filter1) |
            Q(phylum__icontains=filter1) |
            Q(slab__slab_no__icontains=filter1)
        )

    # Order by slab number and specimen number
    specimen_list = specimen_list.order_by('slab__slab_no', 'specimen_no')
    
    # Pre-fetch specimen and slab IDs to use in image counts
    all_specimens = list(specimen_list)
    specimen_ids = [specimen.id for specimen in all_specimens]
    slab_ids = list(set(specimen.slab.id for specimen in all_specimens if specimen.slab))
    
    # Batch query image counts for all specimens and slabs at once
    specimen_image_counts = {}
    slab_image_counts = {}
    
    # Query for specimen image counts
    if specimen_ids:
        specimen_images = SpFossilImage.objects.filter(specimen_id__in=specimen_ids)\
            .values('specimen_id')\
            .annotate(count=Count('id'))
        
        for item in specimen_images:
            specimen_image_counts[item['specimen_id']] = item['count']
    
    # Query for slab-only image counts
    if slab_ids:
        slab_images = SpFossilImage.objects.filter(slab_id__in=slab_ids, specimen__isnull=True)\
            .values('slab_id')\
            .annotate(count=Count('id'))
        
        for item in slab_images:
            slab_image_counts[item['slab_id']] = item['count']

    # Group specimens by slab
    grouped_specimens = []
    for slab_id, group in groupby(all_specimens, key=lambda x: (x.slab.id if x.slab else None)):
        group_list = list(group)
        slab = group_list[0].slab if group_list[0].slab else None
        
        # Assign pre-fetched image counts to specimens
        for specimen in group_list:
            specimen.image_count = specimen_image_counts.get(specimen.id, 0)
        
        # Get pre-fetched slab-only image count
        slab_only_image_count = 0
        if slab:
            slab_only_image_count = slab_image_counts.get(slab.id, 0)
        
        grouped_specimens.append({
            'slab': slab,
            'specimens': group_list,
            'slab_only_image_count': slab_only_image_count
        })

    # Paginate the grouped results
    paginator = Paginator(grouped_specimens, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(page_no)

    context = {
        'user_obj': user_obj,
        'page_obj': page_obj,
        'filter1': filter1,
        'filter2': filter2,
        'grouped_specimens': page_obj,  # Now we pass grouped specimens instead
    }
    return render(request, 'siriuspasset/specimen_list.html', context)

def specimen_detail(request, specimen_id):
    user_obj = get_user_obj(request)
    specimen = get_object_or_404(SpFossilSpecimen, pk=specimen_id)
    
    # Get images
    images = SpFossilImage.objects.filter(specimen=specimen)
    
    # Sort images by filename pattern
    sorted_images = sort_images_by_filename(list(images))
    
    # Group images into rows for the gallery (3 images per row)
    IMAGES_PER_ROW = 3
    image_rows = [sorted_images[i:i + IMAGES_PER_ROW] for i in range(0, len(sorted_images), IMAGES_PER_ROW)]
    
    # Convert history records to a list to support indexing operations in template
    history_records = list(specimen.history.all())
    
    context = {
        'specimen': specimen,
        'user_obj': user_obj,
        'image_rows': image_rows,
        'total_images': len(sorted_images),
        'history_records': history_records,
        'debug_info': {
            'specimen_id': specimen_id,
            'image_count': len(sorted_images)
        }
    }
    
    return render(request, 'siriuspasset/specimen_detail.html', context)


def add_specimen(request):
    user_obj = get_user_obj(request)
    errors = []
    existing_slab_id = request.GET.get('slab_id')
    
    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debug print
        print("Files:", request.FILES)     # Debug print
        
        slab_choice = request.POST.get('slab_choice')
        print("Slab Choice:", slab_choice)  # Debug print
        
        specimen_form = SpFossilSpecimenForm(request.POST, request.FILES)
        print("Specimen Form Valid:", specimen_form.is_valid())  # Debug print
        if not specimen_form.is_valid():
            print("Specimen Form Errors:", specimen_form.errors)  # Debug print
        
        if slab_choice == 'existing':
            existing_slab_id = request.POST.get('existing_slab')
            print("Existing Slab ID:", existing_slab_id)  # Debug print
            try:
                slab = SpSlab.objects.get(id=existing_slab_id)
                slab_form = None
            except (SpSlab.DoesNotExist, ValueError) as e:
                print("Slab Error:", str(e))  # Debug print
                errors.append('Selected slab does not exist')
                slab_form = SpSlabForm()
                slab = None
        else:  # new slab
            slab_form = SpSlabForm(request.POST)
            print("Slab Form Valid:", slab_form.is_valid())  # Debug print
            if not slab_form.is_valid():
                print("Slab Form Errors:", slab_form.errors)  # Debug print
            slab = None
            if not request.POST.get('slab_no'):
                errors.append('Slab number is required')
        
        if not request.POST.get('specimen_no'):
            errors.append('Specimen number is required')
            
        if specimen_form.is_valid() and (slab_choice == 'existing' and slab or (slab_form and slab_form.is_valid())):
            try:
                with transaction.atomic():
                    if slab_choice != 'existing':
                        slab = slab_form.save(commit=False)
                        # Set IP address
                        slab.created_ip = get_client_ip(request)
                        slab.modified_ip = get_client_ip(request)
                        # Set change reason for history
                        slab._change_reason = "Initial creation"
                        slab.save()
                    
                    specimen = specimen_form.save(commit=False)
                    specimen.slab = slab
                    # Set IP address
                    specimen.created_ip = get_client_ip(request)
                    specimen.modified_ip = get_client_ip(request)
                    # Set change reason for history
                    specimen._change_reason = "Initial creation"
                    specimen.save()
                return HttpResponseRedirect('/siriuspasset/specimen_list')
            except Exception as e:
                print("Save Error:", str(e))  # Debug print
                errors.append(f'Error saving data: {str(e)}')
        else:
            if slab_choice != 'existing' and slab_form:
                for field, error_list in slab_form.errors.items():
                    for error in error_list:
                        errors.append(f'Slab {field}: {error}')
            for field, error_list in specimen_form.errors.items():
                for error in error_list:
                    errors.append(f'Specimen {field}: {error}')
    else:
        slab_form = SpSlabForm()
        specimen_form = SpFossilSpecimenForm()
        
        if existing_slab_id:
            try:
                existing_slab = SpSlab.objects.get(id=existing_slab_id)
            except SpSlab.DoesNotExist:
                existing_slab = None
        else:
            existing_slab = None
    
    # Get list of all slabs for the dropdown
    all_slabs = SpSlab.objects.all().order_by('slab_no')
    
    return render(request, 'siriuspasset/specimen_form.html', {
        'slab_form': slab_form,
        'specimen_form': specimen_form,
        'user_obj': user_obj,
        'errors': errors,
        'all_slabs': all_slabs,
        'existing_slab': existing_slab if 'existing_slab' in locals() else None,
    })


def edit_specimen(request,pk):
    user_obj = get_user_obj(request)
    specimen = get_object_or_404(SpFossilSpecimen, pk=pk)
    
    if request.method == 'POST':
        specimen_form = SpFossilSpecimenForm(request.POST, request.FILES, instance=specimen)
        
        # Create a list to hold any errors
        form_errors = []
        
        if specimen_form.is_valid():
            specimen = specimen_form.save(commit=False)
            # Set IP address
            specimen.modified_ip = get_client_ip(request)
            # Set change reason for history
            specimen._change_reason = "Edit via web interface"
            specimen.save()
            
            # Handle image uploads
            uploaded_images = request.FILES.getlist('specimen_images')
            if uploaded_images:
                for image_file in uploaded_images:
                    # Create a new image instance
                    image = SpFossilImage(
                        specimen=specimen,
                        slab=specimen.slab,
                        image_file=image_file,
                        description=f"Uploaded via web interface"
                    )
                    try:
                        image.save()
                    except Exception as e:
                        form_errors.append(f"Error saving image {image_file.name}: {str(e)}")
            
            if not form_errors:
                return HttpResponseRedirect('/siriuspasset/specimen_detail/'+str(specimen.id))
        else:
            form_errors.extend([f"{field}: {error}" for field, errors in specimen_form.errors.items() for error in errors])
    else:
        specimen_form = SpFossilSpecimenForm(instance=specimen)
        form_errors = []

    # Get list of all slabs for the dropdown
    all_slabs = SpSlab.objects.all().order_by('slab_no')
    
    # Get a form for the slab (read-only)
    slab_form = SpSlabForm(instance=specimen.slab)
    for field in slab_form.fields.values():
        field.disabled = True
    
    # Get existing images
    existing_images = SpFossilImage.objects.filter(specimen=specimen)
    
    return render(request, 'siriuspasset/specimen_form.html', {
        'specimen_form': specimen_form,
        'slab_form': slab_form,
        'user_obj': user_obj,
        'all_slabs': all_slabs,
        'existing_slab': specimen.slab,
        'editing': True,
        'existing_images': existing_images,
        'errors': form_errors
    })

def delete_specimen(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(SpFossilSpecimen, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/siriuspasset/specimen_list')

def slab_detail(request, slab_id):
    user_obj = get_user_obj(request)
    slab = get_object_or_404(SpSlab, pk=slab_id)
    
    # Get only slab images (those without specimen foreign key)
    slab_only_images = SpFossilImage.objects.filter(slab=slab, specimen__isnull=True)
    
    # Sort slab images by filename pattern
    sorted_slab_images = sort_images_by_filename(list(slab_only_images))
    print(f"Found {len(sorted_slab_images)} slab-only images for slab {slab.slab_no}")  # Debug print
    
    # Group slab images into rows for the gallery (3 images per row)
    IMAGES_PER_ROW = 3
    slab_image_rows = [sorted_slab_images[i:i + IMAGES_PER_ROW] for i in range(0, len(sorted_slab_images), IMAGES_PER_ROW)]
    
    # Get specimens with their images
    specimens = slab.specimens.all().order_by('specimen_no')
    specimen_with_images = []
    
    for specimen in specimens:
        # Get images for this specimen
        spec_images = SpFossilImage.objects.filter(specimen=specimen)
        
        # Sort specimen images by filename pattern
        sorted_spec_images = sort_images_by_filename(list(spec_images))
        
        spec_image_rows = [sorted_spec_images[i:i + IMAGES_PER_ROW] for i in range(0, len(sorted_spec_images), IMAGES_PER_ROW)]
        
        specimen_with_images.append({
            'specimen': specimen,
            'image_rows': spec_image_rows,
            'total_images': len(sorted_spec_images)
        })
    
    # Convert history records to a list to support indexing operations in template
    history_records = list(slab.history.all())
    
    context = {
        'slab': slab,
        'user_obj': user_obj,
        'slab_image_rows': slab_image_rows,
        'slab_total_images': len(sorted_slab_images),
        'specimens_with_images': specimen_with_images,
        'history_records': history_records,
        'debug_info': {
            'slab_id': slab_id,
            'slab_image_count': len(sorted_slab_images),
            'specimen_count': specimens.count(),
            'slab_no': slab.slab_no
        }
    }
    
    return render(request, 'siriuspasset/slab_detail.html', context)

def add_slab(request):
    """Add a new slab"""
    user_obj = get_user_obj(request)
    
    if request.method == 'POST':
        form = SpSlabForm(request.POST)
        if form.is_valid():
            slab = form.save(commit=False)
            # Set IP address
            slab.created_ip = get_client_ip(request)
            slab.modified_ip = get_client_ip(request)
            # Set change reason for history
            slab._change_reason = "Initial creation"
            slab.save()
            return HttpResponseRedirect(f'/siriuspasset/slab_detail/{slab.id}')
    else:
        form = SpSlabForm()
    
    return render(request, 'siriuspasset/slab_form.html', {
        'slab_form': form,
        'user_obj': user_obj,
        'slab': None
    })

def edit_slab(request, pk):
    """Edit slab information"""
    user_obj = get_user_obj(request)
    slab = get_object_or_404(SpSlab, pk=pk)
    
    # Create a list to hold any errors
    form_errors = []

    if request.method == 'POST':
        form = SpSlabForm(request.POST, request.FILES, instance=slab)
        if form.is_valid():
            slab = form.save(commit=False)
            # Set IP address
            slab.modified_ip = get_client_ip(request)
            # Set change reason for history
            slab._change_reason = "Edit via web interface"
            slab.save()
            
            # Handle image uploads
            uploaded_images = request.FILES.getlist('slab_images')
            if uploaded_images:
                for image_file in uploaded_images:
                    # Create a new image instance
                    image = SpFossilImage(
                        slab=slab,
                        specimen=None,  # This is a slab image, not a specimen image
                        image_file=image_file,
                        description=f"Uploaded via web interface"
                    )
                    try:
                        image.save()
                    except Exception as e:
                        form_errors.append(f"Error saving image {image_file.name}: {str(e)}")
            
            if not form_errors:
                return HttpResponseRedirect(f'/siriuspasset/slab_detail/{slab.id}')
        else:
            form_errors.extend([f"{field}: {error}" for field, errors in form.errors.items() for error in errors])
    else:
        form = SpSlabForm(instance=slab)

    # Get existing images for this slab (only those not associated with a specimen)
    existing_images = SpFossilImage.objects.filter(slab=slab, specimen__isnull=True)

    return render(request, 'siriuspasset/slab_form.html', {
        'slab_form': form,
        'user_obj': user_obj,
        'slab': slab,
        'existing_images': existing_images,
        'errors': form_errors
    })

def delete_slab(request, pk):
    """Delete a slab"""
    user_obj = get_user_obj(request)
    slab = get_object_or_404(SpSlab, pk=pk)
    
    # Check if slab has specimens
    if slab.specimens.exists():
        from django.contrib import messages
        messages.error(request, f"Cannot delete slab {slab.slab_no} because it has associated specimens. Delete the specimens first.")
        return HttpResponseRedirect(f'/siriuspasset/slab_detail/{slab.id}')
    
    # Delete the slab
    slab.delete()
    return HttpResponseRedirect('/siriuspasset/specimen_list')

def recent_activities(request):
    """View to display recent activities: images, slab edits, and specimen edits"""
    print("[RECENT_ACTIVITIES] Starting recent activities view")
    start_time = time.time()
    
    user_obj = get_user_obj(request)
    
    # Get filter parameter for time range
    time_range = request.GET.get('range', 'week')  # Default to showing past week
    limit = int(request.GET.get('limit', 50))      # Default to 50 items
    print(f"[RECENT_ACTIVITIES] Time range: {time_range}, limit: {limit}")
    
    # Calculate the date range
    today = datetime.now().date()
    print(f"[RECENT_ACTIVITIES] Current date: {today}")
    
    if time_range == 'day':
        start_date = today - timedelta(days=1)
    elif time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
    elif time_range == 'future':
        # This option is now redundant but kept for compatibility
        start_date = None
        time_range = 'all'  # Convert to 'all' since we're not filtering for future dates
    else:  # 'all'
        start_date = None
    
    print(f"[RECENT_ACTIVITIES] Start date for filtering: {start_date}")
    
    # Query images with dates
    print("[RECENT_ACTIVITIES] Querying recent images")
    recent_images = SpFossilImage.objects.all().select_related('specimen', 'slab')
    
    if start_date:
        recent_images = recent_images.filter(created_on__date__gte=start_date)
    
    # Order by most recent first
    recent_images = recent_images.order_by('-created_on')[:limit]
    print(f"[RECENT_ACTIVITIES] Found {len(recent_images)} recent images")
    
    # Get history records for slabs
    print("[RECENT_ACTIVITIES] Querying slab history")
    from siriuspasset.models import SpSlab
    slab_history = SpSlab.history.all()
    print(f"[RECENT_ACTIVITIES] Initial slab history query returned {slab_history.count()} records")
    
    if start_date:
        # Add a one-hour buffer to avoid timezone issues
        from datetime import time as dt_time
        start_datetime = datetime.combine(start_date, dt_time.min) - timedelta(hours=1)
        print(f"[RECENT_ACTIVITIES] Using buffer-adjusted start_datetime: {start_datetime} for comparison")
        
        # Debug the date formats of some history records
        for i, record in enumerate(slab_history[:2]):
            print(f"[RECENT_ACTIVITIES] Sample record date format: {record.history_date} (type: {type(record.history_date)})")
        
        # Filter using the datetime object with buffer
        slab_history = slab_history.filter(history_date__gte=start_datetime)
        print(f"[RECENT_ACTIVITIES] After date filter ({start_date}), slab history has {slab_history.count()} records")
    
    slab_history = slab_history.order_by('-history_date')[:limit]
    print(f"[RECENT_ACTIVITIES] Found {len(slab_history)} slab history records after ordering and limiting")
    
    # Debug: Log some sample slab history records
    for i, record in enumerate(slab_history[:3]):
        print(f"[RECENT_ACTIVITIES] Sample slab history #{i+1}: ID={record.id}, history_id={record.history_id}, "
              f"type={record.history_type}, date={record.history_date}, slab_no={record.slab_no}")
    
    # Get history records for specimens
    print("[RECENT_ACTIVITIES] Querying specimen history")
    from siriuspasset.models import SpFossilSpecimen
    specimen_history = SpFossilSpecimen.history.all()
    print(f"[RECENT_ACTIVITIES] Initial specimen history query returned {specimen_history.count()} records")
    
    if start_date:
        # Use the same adjusted start_datetime with buffer
        specimen_history = specimen_history.filter(history_date__gte=start_datetime)
        print(f"[RECENT_ACTIVITIES] After date filter ({start_date}), specimen history has {specimen_history.count()} records")
    
    specimen_history = specimen_history.order_by('-history_date')[:limit]
    print(f"[RECENT_ACTIVITIES] Found {len(specimen_history)} specimen history records after ordering and limiting")
    
    # Debug: Log some sample specimen history records
    for i, record in enumerate(specimen_history[:3]):
        print(f"[RECENT_ACTIVITIES] Sample specimen history #{i+1}: ID={record.id}, history_id={record.history_id}, "
              f"type={record.history_type}, date={record.history_date}, specimen_no={record.specimen_no}")
    
    # Prepare context for display
    activities = []
    
    # Process image activities
    print("[RECENT_ACTIVITIES] Processing image activities")
    image_count = 0
    for image in recent_images:
        activity = {
            'image': image,
            'date': image.created_on,
            'thumbnail_url': image.get_thumbnail_url(),
            'type': 'image',
            'action': 'added',
        }
        
        # Determine if this is a specimen image or slab image
        if image.specimen:
            activity['associated_with'] = 'specimen'
            activity['specimen'] = image.specimen
            activity['detail_url'] = reverse('siriuspasset:specimen_detail', args=[image.specimen.id])
        elif image.slab:
            activity['associated_with'] = 'slab'
            activity['slab'] = image.slab
            activity['detail_url'] = reverse('siriuspasset:slab_detail', args=[image.slab.id])
        
        activities.append(activity)
        image_count += 1
    
    print(f"[RECENT_ACTIVITIES] Processed {image_count} image activities")
    
    # Process slab history activities
    print("[RECENT_ACTIVITIES] Processing slab history activities")
    slab_count = 0
    for record in slab_history:
        try:
            # Debug record details
            print(f"[RECENT_ACTIVITIES] Processing slab history: ID={record.id}, type={record.history_type}, "
                  f"history_id={record.history_id}, date={record.history_date}")
            
            # Check if record.history_user exists
            if hasattr(record, 'history_user'):
                user_info = record.history_user.username if record.history_user else "Unknown"
            else:
                user_info = "No history_user attribute"
                print(f"[RECENT_ACTIVITIES] Warning: history_user attribute missing on slab history record {record.id}")
            
            activity = {
                'date': record.history_date,
                'type': 'slab',
                'action': record.history_type,  # '+' for created, '~' for modified, '-' for deleted
                'slab_no': record.slab_no,
                'record_id': record.id,
                'instance_id': record.history_id,
                'detail_url': reverse('siriuspasset:slab_detail', args=[record.history_id]),
                'user': user_info,
                'associated_with': 'slab',
            }
            
            # Determine action text
            if record.history_type == '+':
                activity['action_text'] = 'created'
            elif record.history_type == '~':
                activity['action_text'] = 'modified'
            elif record.history_type == '-':
                activity['action_text'] = 'deleted'
                # For deleted records, we don't have a valid URL
                activity['detail_url'] = '#'
            
            activities.append(activity)
            slab_count += 1
            print(f"[RECENT_ACTIVITIES] Successfully added slab activity for {record.slab_no}, action={record.history_type}")
        except Exception as e:
            print(f"[RECENT_ACTIVITIES] Error processing slab history record {record.id}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    print(f"[RECENT_ACTIVITIES] Processed {slab_count} slab history activities")
    
    # Process specimen history activities
    print("[RECENT_ACTIVITIES] Processing specimen history activities")
    specimen_count = 0
    for record in specimen_history:
        try:
            # Debug record details
            print(f"[RECENT_ACTIVITIES] Processing specimen history: ID={record.id}, type={record.history_type}, "
                  f"history_id={record.history_id}, date={record.history_date}")
            
            # Check if record.history_user exists
            if hasattr(record, 'history_user'):
                user_info = record.history_user.username if record.history_user else "Unknown"
            else:
                user_info = "No history_user attribute"
                print(f"[RECENT_ACTIVITIES] Warning: history_user attribute missing on specimen history record {record.id}")
            
            activity = {
                'date': record.history_date,
                'type': 'specimen',
                'action': record.history_type,  # '+' for created, '~' for modified, '-' for deleted
                'specimen_no': record.specimen_no,
                'taxon_name': record.taxon_name,
                'record_id': record.id,
                'instance_id': record.history_id,
                'slab_id': record.slab_id,
                'detail_url': reverse('siriuspasset:specimen_detail', args=[record.history_id]),
                'user': user_info,
                'associated_with': 'specimen',
            }
            
            # Determine action text
            if record.history_type == '+':
                activity['action_text'] = 'created'
            elif record.history_type == '~':
                activity['action_text'] = 'modified'
            elif record.history_type == '-':
                activity['action_text'] = 'deleted'
                # For deleted records, we don't have a valid URL
                activity['detail_url'] = '#'
            
            activities.append(activity)
            specimen_count += 1
            print(f"[RECENT_ACTIVITIES] Successfully added specimen activity for {record.specimen_no}, action={record.history_type}")
        except Exception as e:
            print(f"[RECENT_ACTIVITIES] Error processing specimen history record {record.id}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    print(f"[RECENT_ACTIVITIES] Processed {specimen_count} specimen history activities")
    
    # Sort all activities by date, most recent first
    print("[RECENT_ACTIVITIES] Sorting activities by date")
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    # Limit the total number of activities
    activities = activities[:limit]
    
    # Debug log the final activities structure
    print(f"[RECENT_ACTIVITIES] Final activities list contains {len(activities)} items")
    activity_types = {}
    for i, activity in enumerate(activities[:5]):  # Log first 5 for debugging
        print(f"[RECENT_ACTIVITIES] Activity #{i+1}: type={activity['type']}, " +
              f"action={activity.get('action', 'N/A')}, date={activity['date']}")
        # Count by type
        activity_type = activity['type']
        if activity_type not in activity_types:
            activity_types[activity_type] = 0
        activity_types[activity_type] += 1
    
    # Log activity type counts
    print("[RECENT_ACTIVITIES] Activity counts by type:")
    for activity_type, count in activity_types.items():
        print(f"[RECENT_ACTIVITIES]   - {activity_type}: {count}")
    
    context = {
        'user_obj': user_obj,
        'activities': activities,
        'time_range': time_range,
        'total_activities': len(activities),
        'debug_info': {
            'has_image_activities': any(activity['type'] == 'image' for activity in activities),
            'has_slab_activities': any(activity['type'] == 'slab' for activity in activities),
            'has_specimen_activities': any(activity['type'] == 'specimen' for activity in activities),
            'sample_activity': activities[0] if activities else None
        }
    }
    
    end_time = time.time()
    print(f"[RECENT_ACTIVITIES] Finished in {end_time - start_time:.2f} seconds with {len(activities)} total activities")
    
    return render(request, 'siriuspasset/recent_activities.html', context)

def directory_scan_list(request):
    """View to display a history of directory scans"""
    user_obj = get_user_obj(request)
    
    # Get scan history
    scans = DirectoryScan.objects.order_by('-scan_start_time')
    
    # Pagination
    page_no = int(request.GET.get('page', 1))
    paginator = Paginator(scans, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(page_no)
    
    context = {
        'user_obj': user_obj,
        'page_obj': page_obj,
        'scans': page_obj,
        'total_scans': scans.count(),
    }
    
    return render(request, 'siriuspasset/directory_scan_list.html', context)

def directory_scan_detail(request, scan_id):
    """View to display details of a specific directory scan"""
    user_obj = get_user_obj(request)
    scan = get_object_or_404(DirectoryScan, pk=scan_id)
    
    context = {
        'user_obj': user_obj,
        'scan': scan,
    }
    
    return render(request, 'siriuspasset/directory_scan_detail.html', context)

def delete_image(request, image_id):
    """
    View to delete an image via AJAX request
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'})
    
    try:
        image = get_object_or_404(SpFossilImage, pk=image_id)
        
        # Get the specimen ID before deletion for redirection purposes
        specimen_id = None
        if image.specimen:
            specimen_id = image.specimen.id
        
        # Get the image file path for deletion
        image_path = image.image_file.path if image.image_file else None
        
        # Delete the image record from the database
        image.delete()
        
        # Delete the actual file if it exists
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            
            # Try to delete the thumbnail if it exists
            thumbnail_path = os.path.join(os.path.dirname(image_path), 'thumbnails', os.path.basename(image_path))
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def recent_photos(request):
    """View to display recently added photos in descending order of creation date"""
    user_obj = get_user_obj(request)
    
    # Get filter parameters
    time_range = request.GET.get('range', 'week')  # Default to showing past week
    limit = int(request.GET.get('limit', 50))      # Default to 50 items
    
    # Calculate the date range
    today = datetime.now().date()
    
    if time_range == 'day':
        start_date = today - timedelta(days=1)
    elif time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
    elif time_range == 'show_all':
        # Special option to explicitly show all images, bypass date filtering completely
        start_date = None
    else:  # 'all'
        start_date = None
    
    # Query images with efficient database filtering
    recent_images_query = SpFossilImage.objects.all().select_related('specimen', 'slab')
    
    # Apply date filtering at the database level if needed
    if start_date:
        # Convert to datetime to catch all records from that day
        from datetime import time
        start_datetime = datetime.combine(start_date, time.min)  # e.g., 2023-01-01 00:00:00
        
        # Use standard Django ORM filtering
        recent_images_query = recent_images_query.filter(created_on__gte=start_datetime)
    
    # Apply sorting and limiting at the database level
    recent_images = recent_images_query.order_by('-created_on')[:limit]
    
    # Process the results efficiently
    photos = []
    for image in recent_images:
        photo = {
            'image': image,
            'thumbnail_url': image.get_thumbnail_url(),
            'created_on': image.created_on,
            'file_name': os.path.basename(image.original_path) if hasattr(image, 'original_path') and image.original_path else (os.path.basename(image.image_file.name) if image.image_file else "Unknown"),
            'file_size': image.image_file.size if image.image_file else 0,
        }
        
        # Determine if this is a specimen image or slab image
        if image.specimen:
            photo['associated_with'] = 'specimen'
            photo['specimen'] = image.specimen
            photo['detail_url'] = reverse('siriuspasset:specimen_detail', args=[image.specimen.id])
            photo['specimen_no'] = image.specimen.specimen_no
            photo['taxon_name'] = image.specimen.taxon_name
        elif image.slab:
            photo['associated_with'] = 'slab'
            photo['slab'] = image.slab
            photo['detail_url'] = reverse('siriuspasset:slab_detail', args=[image.slab.id])
            photo['slab_no'] = image.slab.slab_no
        
        photos.append(photo)
    
    context = {
        'user_obj': user_obj,
        'photos': photos,
        'time_range': time_range,
        'total_photos': len(photos),
        'debug_info': {
            'total_in_db': SpFossilImage.objects.count(),
            'filter_date': start_date,
            'current_date': today,
        }
    }
    
    return render(request, 'siriuspasset/recent_photos.html', context)
