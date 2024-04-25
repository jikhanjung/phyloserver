from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import RoseOccurrence, RoseFile
from .forms import RoseOccurrenceForm, RoseFileForm
from django.db.models import Q
from django.core.paginator import Paginator
from nkfcluster.models import ChronoUnit
import json
import os
# Create your views here.
import plotly.graph_objects as go
import numpy as np
import io

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

# Create your views here.
def index(request):
    return HttpResponseRedirect('file_list')

def occ_list(request):
    user_obj = get_user_obj(request)
    #order_by = request.GET.get('order_by', 'year')
    filter1 = request.GET.get('filter1')
    filter2 = request.GET.get('filter2')

    occ_list = RoseOccurrence.objects.all()

    if filter2:
        occ_list = occ_list.filter(Q(source_code=filter2)).distinct()

    if filter1:
        occ_list = occ_list.filter(Q(genus__contains=filter1)).distinct()
        #print(ref_list)

    occ_list = occ_list.order_by( 'locality')

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
    return render(request, 'rose/occ_list.html', context)

def occ_detail(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(RoseOccurrence, pk=occ_id)
    return render(request, 'rose/occ_detail.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = RoseOccurrenceForm(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            #occ=occ_form.save()
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            #occ.process_genus_name()
            occ.save()
                
            return HttpResponseRedirect('/rose/occ_detail/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = RoseOccurrenceForm()
    return render(request, 'rose/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(RoseOccurrence, pk=pk)
    
    if request.method == 'POST':
        occ_form = RoseOccurrenceForm(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            #occ.process_genus_name()
            occ.save()
            return HttpResponseRedirect('/rose/occ_detail/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = RoseOccurrenceForm(instance=occ)

    return render(request, 'rose/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(RoseOccurrence, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/rose/occ_list')

def occ_chart(request, file_id=None):
    user_obj = get_user_obj(request)

    locality = request.POST.get('locality')
    age = request.POST.get('age')

    filter1 = request.GET.get('filter1')
    region = request.GET.get('region')

    #chrono_data = 

    if file_id:
        occ_query = RoseOccurrence.objects.filter(rosefile_id=file_id)
    else:
        occ_query = RoseOccurrence.objects.all()

    if region:
        occ_query = occ_query.filter(Q(region=region))
    if filter1:
        occ_query = occ_query.filter(Q(locality__contains=filter1)|Q(age__contains=filter1))
        #print(ref_list)

    occ_query = occ_query.order_by('locality')

    occ_data = []
    for occ in occ_query:
        occ_data.append( { 'id': occ.id, 'locality': occ.locality, 'age': occ.age, 'comment': occ.comment,
                            'strike': occ.strike, 'dip': occ.dip } ) 

    return render(request, 'rose/occ_chart.html', {'user_obj':user_obj, 'file_id': file_id, 'locality':locality, 'age':age, 'occ_data':json.dumps(occ_data)})

def upload_file(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        file_form = RoseFileForm(request.POST,request.FILES)
        # check whether it's valid:
        if file_form.is_valid():
            file = file_form.save(commit=False)
            #print(phylorun.datafile)
            #print(file.file)
            name = str(file.file)
            #print(name)
            if not file.name:
                file.name = name
                #fname,fext = os.path.splitext(name)
                #print(fname, fext)
                #file.name = fname
            file.save()
            #print(file.file)
            file.process_rows()
            return HttpResponseRedirect('/rose/file_detail/'+str(file.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        file_form = RoseFileForm()

    return render(request, 'rose/rose_upload_file.html', {'file_form': file_form,'user_obj':user_obj})

def file_list(request):
    user_obj = get_user_obj(request)
    #order_by = request.GET.get('order_by', 'year')
    filter1 = request.GET.get('filter1')
    filter2 = request.GET.get('filter2')

    file_list = RoseFile.objects.all()

    if filter2:
        file_list = file_list.filter(Q(source_code=filter2)).distinct()

    if filter1:
        file_list = file_list.filter(Q(genus__contains=filter1)).distinct()
        #print(ref_list)

    file_list = file_list.order_by( '-uploaded_at')
    #for file in file_list:
    #    print(file.name)

    #occ_list = NkfOccurrence.objects.order_by('species_name')


    paginator = Paginator(file_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'file_list': file_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
        'filter1': filter1,
        'filter2': filter2,
    }
    return render(request, 'rose/file_list.html', context)

def file_detail(request, file_id):
    user_obj = get_user_obj(request)
    filter1 = request.GET.get('filter1')
    region = request.GET.get('region')
    #filter2 = request.GET.get('filter2')

    file = get_object_or_404(RoseFile, pk=file_id)

    # select distinct region from RoseOccurrence where rosefile_id = file_id
    region_list = [ occ['region'] for occ in RoseOccurrence.objects.filter(rosefile=file).values('region').distinct() ]

    occ_list = RoseOccurrence.objects.filter(rosefile=file)
    if region:
        occ_list = occ_list.filter(Q(region=region))
    if filter1:
        occ_list = occ_list.filter(Q(locality__contains=filter1)|Q(age__contains=filter1))
        #print(ref_list)
    
    occ_list = occ_list.order_by('locality')

    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'rose/file_detail.html', {'file': file, 'user_obj':user_obj, 'occ_list': occ_list, 'page_obj': page_obj, 'filter1': filter1, 'selected_region': region, 'region_list': region_list })

def rose_image(request):
    user_obj = get_user_obj(request)
    # get latest file
    file = RoseFile.objects.latest('uploaded_at')
    # get region name
    region = request.GET.get('region')
    # get occurrences for region
    occ_list = RoseOccurrence.objects.filter(rosefile=file)
    if region:
        occ_list = occ_list.filter(Q(region=region))




    unit_angle = 30

    # Initialize values
    histo_values = [0] * (180 // unit_angle)  # Use integer division
    theta_values = np.arange(unit_angle / 2, 180 + unit_angle / 2, unit_angle)

    half_unit_angle = round(unit_angle / 2 * 10) / 10

    # Assume occ_data is a list of dictionaries 
    count = 0
    for item in occ_list:
        angle = float(item.strike)#get('strike', -999))  # Handle missing values
        if angle == -999: 
            continue

        count += 1
        if angle < 0:
            angle += 360
        if angle > 180:
            angle %= 180

        idx = int(angle // unit_angle)
        histo_values[idx] += 1  

    # Duplicate values for circular chart
    histo_values_2 = histo_values * 2
    theta_values_2 = np.concatenate((theta_values, theta_values + 180))
    labels = [f"{t - half_unit_angle}°~{t + half_unit_angle}°" for t in theta_values_2]

    tick = round(count / 10) 

    # Create Plotly figure
    fig = go.Figure(data=[
        go.Barpolar(
            r=histo_values_2,
            theta=theta_values_2,
            text=labels,
            name="strike",
            marker_color="rgb(106,81,163)",
        )
    ])

    # Layout settings
    fig.update_layout(
        title="",
        font_size=12,
        legend_font_size=12,
        polar=dict(
            barmode="overlay",
            bargap=0.1,
            radialaxis=dict(dtick=tick),
            angularaxis=dict(direction="clockwise", rotation=90)
        ),
        margin=dict(l=20, r=20, t=30, b=20),
        width=250,
        height=200,
    )
    img_bytes = io.BytesIO()
    fig.write_image(img_bytes, format='png')
    img_bytes.seek(0)  

    # Create an HTTP image response
    response = HttpResponse(img_bytes, content_type='image/png') 
    return response
    #return render(request, 'rose/rose_image.html', {'user_obj':user_obj}