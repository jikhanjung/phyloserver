from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import RoseOccurrence
from .forms import RoseOccurrenceForm
from django.db.models import Q
from django.core.paginator import Paginator
from nkfcluster.models import ChronoUnit
import json

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

# Create your views here.
def index(request):
    return HttpResponseRedirect('occ_list')

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

def occ_chart(request):
    user_obj = get_user_obj(request)

    locality = request.POST.get('locality')
    age = request.POST.get('age')

    #chrono_data = 
    chrono_query = ChronoUnit.objects.all().order_by('-begin')
    chrono_data = []
    for chrono in chrono_query:
        chrono_data.append( { 'name': chrono.name, 'id': chrono.id, 'level': chrono.level, 'begin': chrono.begin, 'end': chrono.end } )
    occ_query = RoseOccurrence.objects.all().order_by('locality')
    occ_data = []
    for occ in occ_query:
        occ_data.append( { 'id': occ.id, 'locality': occ.locality, 'age': occ.age, 'comment': occ.comment,
                            'strike': occ.strike, 'dip': occ.dip } ) 

    return render(request, 'rose/occ_chart.html', {'user_obj':user_obj, 'locality':locality, 'age':age, 'occ_data':json.dumps(occ_data)})