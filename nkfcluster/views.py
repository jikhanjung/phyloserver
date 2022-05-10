from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import NkfOccurrence
from django.core.paginator import Paginator
from .forms import NkfOccurrenceForm

from django.shortcuts import render

# Create your views here.

def index(request):
    return HttpResponseRedirect('occ_list')

def occ_list(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ_list = NkfOccurrence.objects.order_by('index')
    paginator = Paginator(occ_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list.html', context)

def occ_detail(request, occ_id):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = NkfOccurrenceForm(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm()
    return render(request, 'nkfcluster/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence(request,pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm(instance=occ)

    return render(request, 'nkfcluster/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence(request, pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list')

def show_table(request): 
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ_list = NkfOccurrence.objects.order_by('index')
    column_list = ["Stratigraphic unit","Lithology","Fossil group","Species name","남포","송림","황주","수안","곡산","법동","은률-과일","평산-금천","옹진-강령","중화-상원","승호","연산-신평","강서-강동","개천-덕천-순천","구장","맹산","은산","고원-천내","초산-고풍","강계-만포","화평","전천-성간","장진","부전","대흥","신포","혜산","태백"]
    occ_hash = {}
    curr_row = None
    data_list = []
    prev_species_name = ""
    for occ in occ_list:
        if occ.species_name != prev_species_name:
            if curr_row:
                data_list.append(curr_row)
            curr_row = [ occ.get_strat_unit_display(), occ.get_lithology_display(), occ.get_group_display(), occ.species_name ]
            while len(curr_row) < len(column_list):
                curr_row.append('')
        location = occ.get_location_display()
        if location in column_list:
            idx = column_list.index(location)
            curr_row[idx] = 'O'
        prev_species_name = occ.species_name


    return render(request, 'nkfcluster/occ_table.html', {'data_list': data_list,'user_obj':user_obj,'column_list':column_list})
