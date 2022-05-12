from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfLocality
from django.core.paginator import Paginator
from .forms import NkfOccurrenceForm, NkfOccurrenceForm2, NkfOccurrenceForm3, NkfLocalityForm
#from cStringIO import StringIO

import xlsxwriter
from django.shortcuts import render
import numpy as np, pandas as pd
import io
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

def occ_list2(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ_list = NkfOccurrence2.objects.order_by('index')
    paginator = Paginator(occ_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list2.html', context)

def occ_detail2(request, occ_id):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence2, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail2.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence2(request):
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
        occ_form = NkfOccurrenceForm2(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail2/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm2()
    return render(request, 'nkfcluster/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence2(request,pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence2, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm2(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail2/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm2(instance=occ)

    return render(request, 'nkfcluster/occ_form2.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence2(request, pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence2, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list2')

def occ_list3(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ_list = NkfOccurrence3.objects.order_by('index')
    paginator = Paginator(occ_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list3.html', context)

def occ_detail3(request, occ_id):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence3, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail3.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence3(request):
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
        occ_form = NkfOccurrenceForm3(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail3/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm3()
    return render(request, 'nkfcluster/occ_form3.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence3(request,pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence3, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm3(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail3/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm3(instance=occ)

    return render(request, 'nkfcluster/occ_form3.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence3(request, pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    occ = get_object_or_404(NkfOccurrence3, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list3')

def show_table(request): 
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    local_regional_select = request.GET.get('local_regional_select')
    genus_species_select = request.GET.get('genus_species_select')

    if genus_species_select != "genus":
        genus_species_select = "species"
        taxon_header = "Species name"
    else:
        genus_species_select = "genus"
        taxon_header = "Genus name"

    if local_regional_select != "regional":
        local_regional_select = "local"
        locality_level = 3
    else:
        local_regional_select = "regional"
        locality_level = 1
    
    locality_list = NkfLocality.objects.filter(level=locality_level).order_by("index")
    locality_name_list = [ loc.name for loc in locality_list ]
    print(locality_name_list)

    occ_list = NkfOccurrence.objects.order_by('index')
    column_list = ["Stratigraphic unit","Lithology","Fossil group",taxon_header]
    column_list.extend(locality_name_list)#,"남포","송림","황주","수안","곡산","법동","은률-과일","평산-금천","옹진-강령","중화-상원","승호-사동","연산-신평","강서-강동","개천-덕천-순천","구장","맹산","은산","고원-천내","초산-고풍","강계-만포","화평","전천-성간","장진","부전","대흥","신포","혜산","태백"]

    occ_hash = {}
    curr_row = None
    data_list = []
    prev_taxon_name = ""
    for occ in occ_list:
        taxon_name = ""
        if genus_species_select == "genus":
            taxon_name = occ.genus_name
        else:
            taxon_name = occ.species_name
        if taxon_name != prev_taxon_name:
            if curr_row:
                data_list.append(curr_row)
            curr_row = [ occ.get_strat_unit_display(), occ.get_lithology_display(), occ.get_group_display(), taxon_name ]
            while len(curr_row) < len(column_list):
                curr_row.append('')
        location = occ.get_location_display()
        if locality_level == 1:
            nkf_location = NkfLocality.objects.filter(name=location)
            if len(nkf_location) >0:
                nkf_location = nkf_location[0]
                while nkf_location.level > 1:
                    nkf_location = nkf_location.parent
                location = nkf_location.name
        if location in column_list:
            idx = column_list.index(location)
            curr_row[idx] = 'O'
        prev_taxon_name = taxon_name

    return render(request, 'nkfcluster/occ_table.html', {'data_list': data_list,'user_obj':user_obj,'column_list':column_list,'genus_species_select':genus_species_select,'local_regional_select':local_regional_select})

def download_cluster(request): 
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    local_regional_select = request.GET.get('local_regional_select')
    genus_species_select = request.GET.get('genus_species_select')

    if genus_species_select != "genus":
        genus_species_select = "species"
        taxon_header = "Species name"
    else:
        genus_species_select = "genus"
        taxon_header = "Genus name"

    if local_regional_select != "regional":
        local_regional_select = "local"
        locality_level = 3
    else:
        local_regional_select = "regional"
        locality_level = 1
    
    locality_list = NkfLocality.objects.filter(level=locality_level).order_by("index")
    locality_name_list = [ loc.name for loc in locality_list ]
    print(locality_name_list)

    occ_list = NkfOccurrence.objects.order_by('index')
    column_list = ["Stratigraphic unit","Lithology","Fossil group",taxon_header]
    column_list.extend(locality_name_list)#,"남포","송림","황주","수안","곡산","법동","은률-과일","평산-금천","옹진-강령","중화-상원","승호-사동","연산-신평","강서-강동","개천-덕천-순천","구장","맹산","은산","고원-천내","초산-고풍","강계-만포","화평","전천-성간","장진","부전","대흥","신포","혜산","태백"]
    occ_hash = {}
    curr_row = None
    data_list = []
    prev_taxon_name = ""
    for occ in occ_list:
        taxon_name = ""
        if genus_species_select == "genus":
            taxon_name = occ.genus_name
        else:
            taxon_name = occ.species_name
        if taxon_name != prev_taxon_name:
            if curr_row:
                data_list.append(curr_row)
            curr_row = [ occ.get_strat_unit_display(), occ.get_lithology_display(), occ.get_group_display(), taxon_name ]
            while len(curr_row) < len(column_list):
                curr_row.append('0')
        location = occ.get_location_display()
        if locality_level == 1:
            nkf_location = NkfLocality.objects.filter(name=location)
            if len(nkf_location) >0:
                nkf_location = nkf_location[0]
                while nkf_location.level > 1:
                    nkf_location = nkf_location.parent
                location = nkf_location.name
        if location in column_list:
            idx = column_list.index(location)
            curr_row[idx] = '1'
        prev_taxon_name = taxon_name
    
    cluster_data = []
    for col_name in column_list[4:]:
        cluster_data.append([col_name])

    for row in data_list:
        occ_data = row[4:]
        for idx in range(len(occ_data)):
            cluster_data[idx].append(occ_data[idx])

    import datetime
    today = datetime.datetime.now()
    date_str = today.strftime("%Y%m%d_%H%M%S")
    buffer = io.BytesIO()

    filename = 'cluster_data_{}.xlsx'.format(date_str)
    doc = xlsxwriter.Workbook(buffer)
    worksheet = doc.add_worksheet()
    row_index = 0
    column_index = 0

    for row_idx in range(len(cluster_data)):
        for col_idx in range(len(cluster_data[0])):
            worksheet.write(row_idx,col_idx,cluster_data[row_idx][col_idx])

    doc.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=filename)

    return render(request, 'nkfcluster/occ_cluster.html', {'cluster_data': cluster_data,'user_obj':user_obj,'column_list':column_list})


def locality_list(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    locality_list = NkfLocality.objects.order_by('index')
    paginator = Paginator(locality_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'locality_list': locality_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/locality_list.html', context)

def locality_detail(request, pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    locality = get_object_or_404(NkfLocality, pk=pk)
    return render(request, 'nkfcluster/locality_detail.html', {'locality': locality, 'user_obj':user_obj})


def add_locality(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        locality_form = NkfLocalityForm(request.POST,request.FILES)
        # check whether it's valid:
        if locality_form.is_valid():
            locality=locality_form.save()
                
            return HttpResponseRedirect('/nkfcluster/locality_detail/'+str(locality.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        locality_form = NkfLocalityForm()
    return render(request, 'nkfcluster/locality_form.html', {'locality_form': locality_form,'user_obj':user_obj})


def edit_locality(request,pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    #print("edit run")
    locality = get_object_or_404(NkfLocality, pk=pk)
    
    if request.method == 'POST':
        locality_form = NkfLocalityForm(request.POST,request.FILES,instance=locality)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if locality_form.is_valid():
            #print("run form valid")
            locality = locality_form.save()
            return HttpResponseRedirect('/nkfcluster/locality_detail/'+str(locality.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        locality_form = NkfLocalityForm(instance=locality)

    return render(request, 'nkfcluster/locality_form.html', {'locality_form': locality_form,'user_obj':user_obj})

def delete_locality(request, pk):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    locality = get_object_or_404(NkfLocality, pk=pk)
    locality.delete()
    return HttpResponseRedirect('/nkfcluster/locality_list')
