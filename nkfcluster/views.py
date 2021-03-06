from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import NkfOccurrence, NkfOccurrence2, NkfOccurrence3, NkfOccurrence4, NkfOccurrence5, NkfOccurrence6, NkfLocality, STRATUNIT_CHOICES, GROUP_CHOICES, PbdbOccurrence, TotalOccurrence, ChronoUnit
from django.core.paginator import Paginator
from .forms import NkfOccurrenceForm, NkfOccurrenceForm2, NkfOccurrenceForm3, NkfOccurrenceForm4, NkfOccurrenceForm5, NkfLocalityForm, ChronoUnitForm, PbdbOccurrenceForm
from django.urls import reverse
#from cStringIO import StringIO
from django.db.models import Q

import xlsxwriter
from django.shortcuts import render
import numpy as np, pandas as pd
import io
import csv 
import datetime

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
    return HttpResponseRedirect('occ_list')

def nkdata_download(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence.objects.order_by('id')

    today = datetime.datetime.now()
    date_str = today.strftime("%Y%m%d_%H%M%S")
    buffer = io.BytesIO()

    filename = 'nk_data_{}.xlsx'.format(date_str)
    doc = xlsxwriter.Workbook(buffer)
    worksheet = doc.add_worksheet()
    row_idx = 0
    #column_index = 0

    col_list = ['strat_unit','strat_unit_code','lithology','lithology_code','fossil_group','group_code','location','location_code',
                'chronounit','chronounit_id','species_name','genus_name','revised_species_name','revised_genus_name','source']

    worksheet.write_row(row_idx, 0, col_list )
    row_idx += 1

    for occ in occ_list:
        #for col_idx in range(len(col_list)):
        if not occ.chronounit:
            unit = ''
            unit_id = ''
        else:
            unit = occ.chronounit.name
            unit_id = occ.chronounit.id
        worksheet.write_row(row_idx, 0, [occ.get_strat_unit_display(), occ.strat_unit, occ.get_lithology_display(), occ.lithology, 
                         occ.get_group_display(), occ.group, occ.get_location_display(), occ.location, unit, unit_id, 
                         occ.species_name, occ.genus_name, occ.revised_species_name, occ.revised_genus_name, occ.source])
        row_idx += 1

    doc.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=filename)


def occ_list(request):
    user_obj = get_user_obj(request)
    #order_by = request.GET.get('order_by', 'year')
    filter1 = request.GET.get('filter1')
    filter2 = request.GET.get('filter2')

    occ_list = NkfOccurrence.objects.all()

    if filter2:
        occ_list = occ_list.filter(Q(source_code=filter2)).distinct()

    if filter1:
        occ_list = occ_list.filter(Q(species_name__contains=filter1)|Q(revised_species_name__contains=filter1)).distinct()
        #print(ref_list)

    occ_list = occ_list.order_by( 'species_name')

    #occ_list = NkfOccurrence.objects.order_by('species_name')


    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
        'filter1': filter1,
        'filter2': filter2,
    }
    return render(request, 'nkfcluster/occ_list.html', context)

def occ_detail(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = NkfOccurrenceForm(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            #occ=occ_form.save()
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            occ.process_genus_name()
            occ.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm()
    return render(request, 'nkfcluster/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            occ.process_genus_name()
            occ.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm(instance=occ)

    return render(request, 'nkfcluster/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list')

def occ_list2(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence2.objects.order_by('index')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list2.html', context)

def occ_detail2(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence2, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail2.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence2(request):
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence2, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list2')

def occ_list3(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence3.objects.order_by('index')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list3.html', context)

def occ_detail3(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence3, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail3.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence3(request):
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence3, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list3')

def occ_list4(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence4.objects.order_by('index')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list4.html', context)

def occ_detail4(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence4, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail4.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence4(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = NkfOccurrenceForm4(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail4/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm4()
    return render(request, 'nkfcluster/occ_form4.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence4(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence4, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm4(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail4/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm4(instance=occ)

    return render(request, 'nkfcluster/occ_form4.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence4(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence4, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list4')


def occ_list5(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence5.objects.order_by('index')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list5.html', context)

def occ_detail5(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence5, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail5.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence5(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = NkfOccurrenceForm5(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail5/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm5()
    return render(request, 'nkfcluster/occ_form5.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence5(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence5, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm5(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail5/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm5(instance=occ)

    return render(request, 'nkfcluster/occ_form5.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence5(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence5, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list5')


def occ_list6(request):
    user_obj = get_user_obj(request)

    occ_list = NkfOccurrence6.objects.order_by('species')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/occ_list6.html', context)

def occ_detail6(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence6, pk=occ_id)
    return render(request, 'nkfcluster/occ_detail6.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence6(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = NkfOccurrenceForm6(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            occ=occ_form.save()
                
            return HttpResponseRedirect('/nkfcluster/occ_detail6/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm6()
    return render(request, 'nkfcluster/occ_form6.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence6(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(NkfOccurrence6, pk=pk)
    
    if request.method == 'POST':
        occ_form = NkfOccurrenceForm6(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save()
            return HttpResponseRedirect('/nkfcluster/occ_detail6/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = NkfOccurrenceForm6(instance=occ)

    return render(request, 'nkfcluster/occ_form6.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence6(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(NkfOccurrence6, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/nkfcluster/occ_list6')    


def locality_list(request):
    user_obj = get_user_obj(request)

    locality_list = NkfLocality.objects.order_by('index')
    paginator = Paginator(locality_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'locality_list': locality_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/locality_list.html', context)

def locality_detail(request, pk):
    user_obj = get_user_obj(request)

    locality = get_object_or_404(NkfLocality, pk=pk)
    return render(request, 'nkfcluster/locality_detail.html', {'locality': locality, 'user_obj':user_obj})


def add_locality(request):
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

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
    user_obj = get_user_obj(request)

    locality = get_object_or_404(NkfLocality, pk=pk)
    locality.delete()
    return HttpResponseRedirect('/nkfcluster/locality_list')

def read_occurrence_data(request):

    #selected_stratunit = []
    strat_keylist = []
    for choice in STRATUNIT_CHOICES:
        val, disp = choice
        strat_keylist.append(val)        
    fossilgroup_keylist = []
    for choice in GROUP_CHOICES:
        val, disp = choice
        fossilgroup_keylist.append(val)        

    selected_stratunit = request.GET.getlist('selected_stratunit')
    if len(selected_stratunit) == 0:
        selected_stratunit = strat_keylist

    selected_fossilgroup = request.GET.getlist('selected_fossilgroup')
    if len(selected_fossilgroup) == 0:
        selected_fossilgroup = fossilgroup_keylist

    #print("selected_stratunit",selected_stratunit)
    locality_level = request.GET.get('locality_level')
    genus_species_select = request.GET.get('genus_species_select')

    if genus_species_select != "genus":
        genus_species_select = "species"
        taxon_header = "Species name"
    else:
        genus_species_select = "genus"
        taxon_header = "Genus name"

    if locality_level not in ['1','2','3']:
        locality_level = 3
    locality_level = int(locality_level)
    
    locality_list = NkfLocality.objects.filter(level=locality_level).order_by("index")
    locality_name_list = [ loc.name for loc in locality_list ]
    #print(locality_name_list)

    occ_list = NkfOccurrence.objects.filter(strat_unit__in=selected_stratunit,group__in=selected_fossilgroup).order_by('strat_unit','group','species_name')
    column_list = ["Stratigraphic unit","Lithology","Fossil group",taxon_header]
    column_list.extend(locality_name_list)

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
        if locality_level < 3:
            nkf_location = NkfLocality.objects.filter(name=location)
            if len(nkf_location) >0:
                nkf_location = nkf_location[0]
                while int(nkf_location.level) > int(locality_level):
                    nkf_location = nkf_location.parent
                location = nkf_location.name
        if location in column_list:
            idx = column_list.index(location)
            curr_row[idx] = 'O'
        prev_taxon_name = taxon_name
    return data_list, column_list, genus_species_select, locality_level, selected_stratunit, selected_fossilgroup

def show_table(request): 
    user_obj = get_user_obj(request)
    
    data_list, column_list, genus_species_select, locality_level, selected_stratunit, selected_fossilgroup = read_occurrence_data(request)
    stratunit_choices = []
    for choice in STRATUNIT_CHOICES:
        val, disp = choice
        stratunit_choices.append( {'value':val,'display': disp})

    fossilgroup_choices = []
    for choice in GROUP_CHOICES:
        val, disp = choice
        fossilgroup_choices.append( {'value':val,'display': disp})
        #stratunit_choices[
    #print(stratunit_choices)
    group_parameter = '&'.join([ 'selected_fossilgroup=' + x for x in selected_fossilgroup ])
    strat_parameter = '&'.join([ 'selected_stratunit=' + x for x in selected_stratunit ])
    urlparameter = { 'fossilgroup': group_parameter, 'stratunit': strat_parameter}

    return render(request, 'nkfcluster/occ_table.html', {'data_list': data_list,'user_obj':user_obj,'column_list':column_list,'genus_species_select':genus_species_select,'locality_level':locality_level,'stratunit_choices':stratunit_choices,'selected_stratunit':selected_stratunit,'fossilgroup_choices':fossilgroup_choices,'selected_fossilgroup':selected_fossilgroup,'urlparameter':urlparameter})

def download_cluster(request): 
    user_obj = get_user_obj(request)

    #data_list, column_list, genus_species_select, locality_level = read_occurrence_data(request)

    data_list, column_list, genus_species_select, locality_level, selected_stratunit, selected_fossilgroup = read_occurrence_data(request)
    stratunit_choices = []
    for choice in STRATUNIT_CHOICES:
        val, disp = choice
        stratunit_choices.append( {'value':val,'display': disp})
    
    fossilgroup_choices = []
    for choice in GROUP_CHOICES:
        val, disp = choice
        fossilgroup_choices.append( {'value':val,'display': disp})


    cluster_data = [['strat_unit'],['fossil_group'],['species_name']]
    for col_name in column_list[4:]:
        cluster_data.append([col_name])

    
    for row in data_list:
        occ_data = [row[0]]
        occ_data.extend(row[2:])
        #print("occ_data len", len(occ_data))
        for idx in range(len(occ_data)):
            cell_value = "0"
            if occ_data[idx] == "O":
                cell_value = "1"
            elif occ_data[idx] == "":
                cell_value = "0"
            else:
                cell_value = occ_data[idx]
            cluster_data[idx].append(cell_value)

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
            worksheet.write(col_idx,row_idx,cluster_data[row_idx][col_idx])

    doc.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=filename)

    return render(request, 'nkfcluster/occ_cluster.html', {'cluster_data': cluster_data,'user_obj':user_obj,'column_list':column_list})

def calculate_cluster(request): 
    user_obj = get_user_obj(request)

    #data_list, column_list, genus_species_select, locality_level = read_occurrence_data(request)

    data_list, column_list, genus_species_select, locality_level, selected_stratunit, selected_fossilgroup = read_occurrence_data(request)
    stratunit_choices = []
    for choice in STRATUNIT_CHOICES:
        val, disp = choice
        stratunit_choices.append( {'value':val,'display': disp})
    
    fossilgroup_choices = []
    for choice in GROUP_CHOICES:
        val, disp = choice
        fossilgroup_choices.append( {'value':val,'display': disp})


    cluster_data = [['strat_unit'],['fossil_group'],['species_name']]
    for col_name in column_list[4:]:
        cluster_data.append([col_name])

    
    for row in data_list:
        occ_data = [row[0]]
        occ_data.extend(row[2:])
        #print("occ_data len", len(occ_data))
        for idx in range(len(occ_data)):
            cell_value = "0"
            if occ_data[idx] == "O":
                cell_value = "1"
            elif occ_data[idx] == "":
                cell_value = "0"
            else:
                cell_value = occ_data[idx]
            cluster_data[idx].append(cell_value)

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
            worksheet.write(col_idx,row_idx,cluster_data[row_idx][col_idx])

    doc.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=filename)


def pbdb_list(request):
    user_obj = get_user_obj(request)
    #order_by = request.GET.get('order_by', 'year')
    filter1 = request.GET.get('filter1')
    #filter2 = request.GET.get('filter2')

    occ_list = PbdbOccurrence.objects.all()

    #if filter2:
    #    occ_list = occ_list.filter(Q(source_code=filter2)).distinct()

    if filter1:
        occ_list = occ_list.filter(Q(species_name__contains=filter1)|Q(revised_species_name__contains=filter1)).distinct()
        #print(ref_list)

    occ_list = occ_list.order_by( 'genus_name', 'species_name')

    #occ_list = PbdbOccurrence.objects.order_by('genus_name','species_name')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
        'filter1': filter1,
        #'filter2': filter2,
    }
    return render(request, 'nkfcluster/pbdb_list.html', context)

def pbdb_detail(request, occ_id):
    user_obj = get_user_obj( request )

    occ = get_object_or_404(PbdbOccurrence, pk=occ_id)
    return render(request, 'nkfcluster/pbdb_detail.html', {'occ': occ, 'user_obj':user_obj})

def edit_pbdb(request,pk):
    user_obj = get_user_obj( request )

    #print("edit run")
    pbdb = get_object_or_404(PbdbOccurrence, pk=pk)
    
    if request.method == 'POST':
        pbdb_form = PbdbOccurrenceForm(request.POST,request.FILES,instance=pbdb)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if pbdb_form.is_valid():
            pbdb = pbdb_form.save(commit=False)
            pbdb.process_genus_name()
            pbdb.save()
            return HttpResponseRedirect('/nkfcluster/pbdb_detail/'+str(pbdb.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        pbdb_form = PbdbOccurrenceForm(instance=pbdb)

    return render(request, 'nkfcluster/pbdb_form.html', {'pbdb_form': pbdb_form,'user_obj':user_obj})


def chronounit_list(request,pk=None):
    user_obj = get_user_obj( request )
    import logging
    logger = logging.getLogger(__name__)
    #reference = get_object_or_404(Reference, pk=reference_id)
    parent = None
    if pk:
        parent = ChronoUnit.objects.get(pk=pk)
        #cnt = parent.get_terminal_unit_count()
        #logger.error('Something went wrong!'+str(cnt))
        chronounit_list = ChronoUnit.objects.filter(parent=pk).order_by('begin')
    else:
        chronounit_list = ChronoUnit.objects.filter(parent=None).order_by('begin')
    for chronounit in chronounit_list:
        if chronounit.terminal_unit_count < 1:
            chronounit.calculate_terminal_unit_count()
    paginator = Paginator(chronounit_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'nkfcluster/chronounit_list.html', {'parent': parent, 'chronounit_list': chronounit_list, 'page_obj': page_obj, 'user_obj': user_obj})

def chronounit_chart(request):
    user_obj = get_user_obj( request )
    chronounit_list = ChronoUnit.objects.filter(parent=None).order_by('begin')
    for chronounit in chronounit_list:
        if chronounit.terminal_unit_count < 1:
            chronounit.calculate_terminal_unit_count()
    return render(request, 'nkfcluster/chronounit_chart.html', {'chronounit_list': chronounit_list, 'user_obj': user_obj})

def chronounit_detail(request,pk):
    user_obj = get_user_obj( request )
    chronounit = get_object_or_404(ChronoUnit, pk=pk)
    return render(request, 'nkfcluster/chronounit_detail.html', {'chronounit': chronounit, 'user_obj': user_obj} )

def chronounit_add(request,pk=None):
    user_obj = get_user_obj( request )
    # if this is a POST request we need to process the form data
    operation = "New"
    if request.method == 'POST':
        
        # create a form instance and populate it with data from the request:
        form = ChronoUnitForm(request.POST)
        #form = ChronoForm(request.POST,instance=chrono)
        # check whether it's valid:
        if form.is_valid():
            #form.save()
            chronounit = form.save(commit=False)
            chronounit.created_by = user_obj.username
            chronounit.save()
            
            return HttpResponseRedirect(reverse('chronounit_list',args=(form.instance.id,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ChronoUnitForm()

    return render(request, 'nkfcluster/chronounit_form.html', {'form': form,'op':operation, 'user_obj': user_obj})

def chronounit_edit(request,pk):
    user_obj = get_user_obj( request )
    # if this is a POST request we need to process the form data
    chrono = get_object_or_404(ChronoUnit, pk=pk)
    operation = "Edit"
    if request.method == 'POST':
        
        # create a form instance and populate it with data from the request:
        form = ChronoUnitForm(request.POST,instance=chrono)
        #form = ChronoForm(request.POST,instance=chrono)
        # check whether it's valid:
        if form.is_valid():
            chronounit = form.save(commit=False)
            chronounit.modified_by = user_obj.username
            chronounit.save()
            return HttpResponseRedirect(reverse('chronounit_list',args=(form.instance.id,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ChronoUnitForm(instance=chrono)

    return render(request, 'nkfcluster/chronounit_form.html', {'form': form,'op':operation, 'user_obj': user_obj})

def chronounit_delete(request, pk):
    user_obj = get_user_obj( request )
    chrono = get_object_or_404(ChronoUnit, pk=pk)
    chrono.delete()
    return HttpResponseRedirect('/nkfcluster/chronounit_list')


def combined_list(request):
    user_obj = get_user_obj( request )

    occ_list = TotalOccurrence.objects.order_by('genus_name','species_name')
    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'occ_list': occ_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'nkfcluster/combined_list.html', context)

def combined_detail(request, occ_id):
    user_obj = get_user_obj( request )

    occ = get_object_or_404(TotalOccurrence, pk=occ_id)
    return render(request, 'nkfcluster/combined_detail.html', {'occ': occ, 'user_obj':user_obj})


def read_combined_data(request):

    #selected_stratunit = []
    chrono_list = [ 'Terreneuvian','Series 2','Miaolingian','Furongian']
    chrono_keylist = chrono_list

    selected_chronounit = request.GET.getlist('selected_chronounit')
    if len(selected_chronounit) == 0:
        selected_chronounit = chrono_keylist

    #print("selected_stratunit",selected_stratunit)
    locality_level = request.GET.get('locality_level') 
    genus_species_select = request.GET.get('genus_species_select')
    exclude_china_only_taxa = request.GET.get('exclude_china_only_taxa') 
    print("china only:",exclude_china_only_taxa)

    if genus_species_select != "genus":
        genus_species_select = "species"
        taxon_header = "Species name"
    else:
        genus_species_select = "genus"
        taxon_header = "Genus name"

    if locality_level not in ['1','2','3']:
        locality_level = 3
    locality_level = int(locality_level)
    
    locality_list = NkfLocality.objects.filter(level=locality_level).order_by("index")
    locality_name_list = [ loc.name for loc in locality_list ]
    locality_name_list.extend( ['NC','SC','BELT','Other'])
    #print(locality_name_list)

    #print(selected_chronounit)
    occ_list = TotalOccurrence.objects.filter(chrono_lvl2__in=selected_chronounit,species_name__gt='').order_by('species_name','genus_name')
    column_list = ["ChronoUnit",taxon_header]
    column_list.extend(locality_name_list)

    occ_hash = {}
    curr_row = None
    data_list = []
    prev_taxon_name = ""
    for occ in occ_list:
        #print(occ.id,occ.species_name,occ.chrono_lvl2,occ.locality_lvl3,occ.genus_name,occ.species_name)
        taxon_name = ""
        if genus_species_select == "genus":
            taxon_name = occ.genus_name
        else:
            taxon_name = occ.species_name
        if taxon_name != prev_taxon_name:
            if curr_row:
                nk_data = curr_row[2:-5]
                nk_data_exist = False
                for nk_cell in nk_data:
                    if nk_cell == 'O':
                        nk_data_exist = True
                #print(nk_data,nk_data_exist)
                if exclude_china_only_taxa != '1' or nk_data_exist:
                    data_list.append(curr_row)
            
            curr_row = [ occ.chrono_lvl2, taxon_name ]
            while len(curr_row) < len(column_list):
                curr_row.append('')
        if locality_level == 1:
            locality = occ.locality_lvl1
        elif locality_level == 2:
            locality = occ.locality_lvl2
        elif locality_level == 3:
            locality = occ.locality_lvl3

        if locality in column_list:
            idx = column_list.index(locality)
            curr_row[idx] = 'O'
        prev_taxon_name = taxon_name
    return data_list, column_list, genus_species_select, locality_level, selected_chronounit, exclude_china_only_taxa

def show_combined_table(request): 
    user_obj = get_user_obj( request )
    
    chrono_list = [ 'Terreneuvian','Series 2','Miaolingian','Furongian']
    data_list, column_list, genus_species_select, locality_level, selected_chronounit, exclude_china_only_taxa = read_combined_data(request)
    chronounit_choices = chrono_list

    chrono_parameter = '&'.join([ 'selected_chronounit=' + x for x in selected_chronounit ])
    urlparameter = { 'chronounit': chrono_parameter}

    return render(request, 'nkfcluster/combined_table.html', {'data_list': data_list,'user_obj':user_obj,'column_list':column_list,'genus_species_select':genus_species_select,'locality_level':locality_level,'chronounit_choices':chronounit_choices,'selected_chronounit':selected_chronounit,'urlparameter':urlparameter,'exclude_china_only_taxa':exclude_china_only_taxa})

def download_combined_cluster(request): 
    user_obj = get_user_obj( request )

    #data_list, column_list, genus_species_select, locality_level = read_occurrence_data(request)
    chrono_list = [ 'Terreneuvian','Series 2','Miaolingian','Furongian']
    data_list, column_list, genus_species_select, locality_level, selected_chronounit,exclude_china_only_taxa = read_combined_data(request)

    #data_list, column_list, genus_species_select, locality_level, selected_stratunit, selected_fossilgroup = read_occurrence_data(request)
    chronounit_choices = chrono_list
    
    cluster_data = [['chrono_unit'],['species_name']]
    for col_name in column_list[2:]:
        cluster_data.append([col_name])

    
    for row in data_list:
        occ_data = [row[0]]
        occ_data.extend(row[1:])
        #print("occ_data len", len(occ_data))
        for idx in range(len(occ_data)):
            cell_value = "0"
            if occ_data[idx] == "O":
                cell_value = "1"
            elif occ_data[idx] == "":
                cell_value = "0"
            else:
                cell_value = occ_data[idx]
            cluster_data[idx].append(cell_value)

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
            worksheet.write(col_idx,row_idx,cluster_data[row_idx][col_idx])

    doc.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=filename)


from django.core.management import call_command

def management_command(request): 
    user_obj = get_user_obj( request )
    message = ''
    if request.method == 'POST':
        command = request.POST.get('command')
        print(command)
        message = call_command(command)
        print("message:", message)

    # if a GET (or any other method) we'll create a blank form
    else:
        pass

    return render(request, 'nkfcluster/management_command.html', { 'message': message,})
