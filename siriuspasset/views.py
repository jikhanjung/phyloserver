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
    
    # Get all images for this specimen
    images = SpFossilImage.objects.filter(specimen=specimen)
    
    # Sort images by filename pattern
    sorted_images = sort_images_by_filename(list(images))
    print(f"Found {len(sorted_images)} images for specimen {specimen.specimen_no}")  # Debug print
    
    # Group images into rows for the gallery (3 images per row)
    IMAGES_PER_ROW = 3
    image_rows = [sorted_images[i:i + IMAGES_PER_ROW] for i in range(0, len(sorted_images), IMAGES_PER_ROW)]
    
    context = {
        'specimen': specimen,
        'user_obj': user_obj,
        'image_rows': image_rows,
        'total_images': len(sorted_images),
        'debug_info': {
            'specimen_id': specimen_id,
            'image_count': len(sorted_images),
            'specimen_no': specimen.specimen_no
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
                        slab = slab_form.save()
                    
                    specimen = specimen_form.save(commit=False)
                    specimen.slab = slab
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

    #print("edit run")
    specimen = get_object_or_404(SpFossilSpecimen, pk=pk)
    
    if request.method == 'POST':
        specimen_form = SpFossilSpecimenForm(request.POST,request.FILES,instance=specimen)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if specimen_form.is_valid():
            #print("run form valid")
            specimen = specimen_form.save(commit=False)
            #reference = form.save(commit=False)
            
            specimen.save()
            return HttpResponseRedirect('/siriuspasset/specimen_detail/'+str(specimen.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        specimen_form = SpFossilSpecimenForm(instance=specimen)

    return render(request, 'siriuspasset/specimen_form.html', {'specimen_form': specimen_form,'user_obj':user_obj})

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
    
    context = {
        'slab': slab,
        'user_obj': user_obj,
        'slab_image_rows': slab_image_rows,
        'slab_total_images': len(sorted_slab_images),
        'specimens_with_images': specimen_with_images,
        'debug_info': {
            'slab_id': slab_id,
            'slab_image_count': len(sorted_slab_images),
            'specimen_count': specimens.count(),
            'slab_no': slab.slab_no
        }
    }
    
    return render(request, 'siriuspasset/slab_detail.html', context)

def recent_activities(request):
    """View to display recent image activities"""
    user_obj = get_user_obj(request)
    
    # Get filter parameter for time range
    time_range = request.GET.get('range', 'week')  # Default to showing past week
    limit = int(request.GET.get('limit', 50))      # Default to 50 items
    
    # Calculate the date range
    today = datetime.now().date()
    if time_range == 'day':
        start_date = today
    elif time_range == 'week':
        start_date = today - timedelta(days=7)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
    else:  # 'all'
        start_date = None
    
    # Query images with dates
    recent_images = SpFossilImage.objects.all().select_related('specimen', 'slab')
    
    if start_date:
        recent_images = recent_images.filter(created_on__date__gte=start_date)
    
    # Order by most recent first
    recent_images = recent_images.order_by('-created_on')[:limit]
    
    # Prepare context for display
    activities = []
    for image in recent_images:
        activity = {
            'image': image,
            'date': image.created_on,
            'thumbnail_url': image.get_thumbnail_url(),
            'type': 'image',
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
    
    context = {
        'user_obj': user_obj,
        'activities': activities,
        'time_range': time_range,
        'total_activities': len(activities),
    }
    
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
