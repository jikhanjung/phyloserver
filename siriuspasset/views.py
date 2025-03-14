from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import SpFossilSpecimen, SpFossilSpecimenImage, SpSlab
from django.core.paginator import Paginator
from .forms import SpFossilSpecimenForm, SpFossilSpecimenImageForm, SpSlabForm
from django.urls import reverse
#from cStringIO import StringIO
from django.db.models import Q
from django.db import transaction
from itertools import groupby
from operator import attrgetter

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

    # Group specimens by slab
    specimens = list(specimen_list)
    grouped_specimens = []
    for slab_id, group in groupby(specimens, key=lambda x: (x.slab.id if x.slab else None)):
        group_list = list(group)
        grouped_specimens.append({
            'slab': group_list[0].slab if group_list[0].slab else None,
            'specimens': group_list
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
    return render(request, 'siriuspasset/specimen_detail.html', {'specimen': specimen, 'user_obj':user_obj})


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