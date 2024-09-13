from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import FrOccurrence, FrFile
from .forms import FrOccurrenceForm, FrFileForm
from django.db.models import Q
from django.core.paginator import Paginator
from nkfcluster.models import ChronoUnit
import json

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
    return HttpResponseRedirect('occ_list')

def occ_list(request):
    user_obj = get_user_obj(request)
    order_by = request.GET.get('order_by', '-period')
    filter1 = request.GET.get('filter1')
    filter2 = request.GET.get('filter2')

    occ_list = FrOccurrence.objects.all()

    if filter2:
        occ_list = occ_list.filter(Q(source_code=filter2)).distinct()

    if filter1:
        occ_list = occ_list.filter(Q(genus__contains=filter1)).distinct()
        #print(ref_list)

    occ_list = occ_list.order_by( order_by )

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
        'order_by': order_by,
    }
    return render(request, 'freshwaterfish/occ_list.html', context)

def occ_detail(request, occ_id):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(FrOccurrence, pk=occ_id)
    return render(request, 'freshwaterfish/occ_detail.html', {'occ': occ, 'user_obj':user_obj})


def add_occurrence(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        occ_form = FrOccurrenceForm(request.POST,request.FILES)
        # check whether it's valid:
        if occ_form.is_valid():
            #occ=occ_form.save()
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            #occ.process_genus_name()
            occ.update_chronounit()
            occ.save()
                
            return HttpResponseRedirect('/freshwaterfish/occ_detail/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = FrOccurrenceForm()
    return render(request, 'freshwaterfish/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})


def edit_occurrence(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    occ = get_object_or_404(FrOccurrence, pk=pk)
    
    if request.method == 'POST':
        occ_form = FrOccurrenceForm(request.POST,request.FILES,instance=occ)
        #print("method POST")
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if occ_form.is_valid():
            #print("run form valid")
            occ = occ_form.save(commit=False)
            #reference = form.save(commit=False)
            #occ.process_genus_name()
            print("occ:", occ, occ.period_code, occ.period, occ.epoch_code, occ.epoch)
            occ.update_chronounit()
            print("occ:", occ, occ.period_code, occ.period, occ.epoch_code, occ.epoch)
            occ.save()
            return HttpResponseRedirect('/freshwaterfish/occ_detail/'+str(occ.id))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        occ_form = FrOccurrenceForm(instance=occ)

    return render(request, 'freshwaterfish/occ_form.html', {'occ_form': occ_form,'user_obj':user_obj})

def delete_occurrence(request, pk):
    user_obj = get_user_obj(request)

    occ = get_object_or_404(FrOccurrence, pk=pk)
    occ.delete()
    return HttpResponseRedirect('/freshwaterfish/occ_list')

def occ_chart(request, file_id=None):
    user_obj = get_user_obj(request)

    x_axis = request.POST.get('x_axis')
    y_axis = request.POST.get('y_axis')

    #chrono_data = 
    chrono_query = ChronoUnit.objects.all().order_by('-begin')
    chrono_data = []
    for chrono in chrono_query:
        chrono_data.append( { 'name': chrono.name, 'id': chrono.id, 'level': chrono.level, 'begin': chrono.begin, 'end': chrono.end } )

    if file_id:
        occ_query = FrOccurrence.objects.filter(frfile_id=file_id).order_by('genus')
    else:
        occ_query = FrOccurrence.objects.all().order_by('genus')

    #occ_query = FrOccurrence.objects.all().order_by('genus')
    occ_data = []
    for occ in occ_query:
        if occ.epoch_code:
            epoch_code_id = occ.epoch_code.id
        else:
            epoch_code_id = None
        if occ.period_code:
            period_code_id = occ.period_code.id
        else:
            period_code_id = None
        occ_data.append( { 'id': occ.id, 'genus': occ.genus, 'locality': occ.locality, 'country': occ.country, 'clade': occ.clade, 'family': occ.family,
                           'origin': occ.origin, 'epoch_code': epoch_code_id, 'period_code': period_code_id,
                            'environment': occ.environment, 'continent': occ.continent } ) 

    return render(request, 'freshwaterfish/occ_chart.html', {'user_obj':user_obj, 'file_id': file_id, 'x_axis':x_axis, 'y_axis':y_axis, 'chrono_data':json.dumps(chrono_data), 'occ_data':json.dumps(occ_data)})


def upload_file(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        file_form = FrFileForm(request.POST,request.FILES)
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
            return HttpResponseRedirect('/freshwaterfish/file_detail/'+str(file.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        file_form = FrFileForm()

    return render(request, 'freshwaterfish/fr_upload_file.html', {'file_form': file_form,'user_obj':user_obj})

def file_list(request):
    user_obj = get_user_obj(request)
    #order_by = request.GET.get('order_by', 'year')
    filter1 = request.GET.get('filter1')
    filter2 = request.GET.get('filter2')

    file_list = FrFile.objects.all()

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
    return render(request, 'freshwaterfish/file_list.html', context)

def file_detail(request, file_id):
    user_obj = get_user_obj(request)
    filter1 = request.GET.get('filter1')
    region = request.GET.get('region')
    #filter2 = request.GET.get('filter2')

    file = get_object_or_404(FrFile, pk=file_id)

    # select distinct region from RoseOccurrence where rosefile_id = file_id
    #region_list = [ occ['region'] for occ in FrOccurrence.objects.filter(frfile=file).values('region').distinct() ]

    occ_list = FrOccurrence.objects.filter(frfile=file)
    #if region:
    #    occ_list = occ_list.filter(Q(region=region))
    #if filter1:
    #    occ_list = occ_list.filter(Q(locality__contains=filter1)|Q(age__contains=filter1))
        #print(ref_list)
    
    occ_list = occ_list.order_by('genus') 

    paginator = Paginator(occ_list, ITEMS_PER_PAGE) # Show ITEMS_PER_PAGE contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'freshwaterfish/file_detail.html', {'file': file, 'user_obj':user_obj, 'occ_list': occ_list, 'page_obj': page_obj, 'filter1': filter1, })
