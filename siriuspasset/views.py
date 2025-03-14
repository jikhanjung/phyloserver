from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import SpFossilSpecimen, SpFossilSpecimenImage, SpSlab
from django.core.paginator import Paginator
from .forms import SpFossilSpecimenForm, SpFossilSpecimenImageForm, SpSlabForm
from django.urls import reverse
#from cStringIO import StringIO
from django.db.models import Q

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

    # 페이지 번호
    page_no = int(request.GET.get('page', 1))

    '''
    if user_obj is None:
        return HttpResponseRedirect(reverse('login'))

    # 검색 조건
    search_str = request.GET.get('search_str', '')
    search_field = request.GET.get('search_field', 'species_name')
    search_field_list = ['species_name', 'revised_species_name', 'location', 'source', 'source_eng']
    if search_field not in search_field_list:
        search_field = 'species_name'

    # 필터링
    filter_str = request.GET.get('filter_str', '')
    filter_field = request.GET.get('filter_field', 'species_name')
    filter_field_list = ['species_name', 'revised_species_name', 'location', 'source', 'source_eng']
    if filter_field not in filter_field_list:
        filter_field = 'species_name'

    # 정렬
    sort_field = request.GET.get('sort_field', 'species_name')
    sort_field_list = ['species_name', 'revised_species_name', 'location', 'source', 'source_eng']
    if sort_field not in sort_field_list:
        sort_field = 'species_name'

    # 정렬 순서
    sort_order = request.GET.get('sort_order', 'asc')
    sort_order_list = ['asc', 'desc']
    if sort_order not in sort_order_list:
        sort_order = 'asc'

    # 필터링
    if filter_str:
        if filter_field == 'species_name':
            specimen_list = SpFossilSpecimen.objects.filter(species_name__icontains=filter_str)
        elif filter_field == 'revised_species_name':
            specimen_list = SpFossilSpecimen.objects.filter(revised_species_name__icontains=filter_str)
        elif filter_field == 'location':
            specimen_list = SpFossilSpecimen.objects.filter(location__icontains=filter_str)
        elif filter_field == 'source':
            specimen_list = SpFossilSpecimen.objects.filter(source__icontains=filter_str)
        elif filter_field == 'source_eng':
            specimen_list = SpFossilSpecimen.objects.filter(source_eng__icontains=filter_str)
    else:
        specimen_list = SpFossilSpecimen.objects.all()

    # 검색
    if search_str:
        if search_field == 'species_name':
            specimen_list = specimen_list.filter(species_name__icontains=search_str)
        elif search_field == 'revised_species_name':
            specimen_list = specimen_list.filter(revised_species_name__icontains=search_str)
        elif search_field == 'location':
            specimen_list = specimen_list.filter(location__icontains=search_str)
        elif search_field == 'source':
            specimen_list = specimen_list.filter(source__icontains=search_str)
        elif search_field == 'source_eng':
            specimen_list = specimen_list.filter(source_eng__icontains=search_str)

    # 정렬
    if sort_order == 'asc':
        specimen_list = specimen_list.order_by(sort_field)
    else:
        specimen_list = specimen_list.order_by('-' + sort_field)'
    '''
    specimen_list = SpFossilSpecimen.objects.all()

    # 페이징 처리
    paginator = Paginator(specimen_list, ITEMS_PER_PAGE)
    page_obj = paginator.get_page(page_no)

    context = {
        'user_obj': user_obj,
        'specimen_list': page_obj,
        #'search_str': search_str,
        #'search_field': search_field,
        #'filter_str': filter_str,
        #'filter_field': filter_field,
        #'sort_field': sort_field,
        #'sort_order': sort_order,        
    }
    return render(request, 'siriuspasset/specimen_list.html', context)

def specimen_detail(request, specimen_id):
    user_obj = get_user_obj(request)

    specimen = get_object_or_404(SpFossilSpecimen, pk=specimen_id)
    return render(request, 'siriuspasset/specimen_detail.html', {'specimen': specimen, 'user_obj':user_obj})


def add_specimen(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        specimen_form = SpFossilSpecimenForm(request.POST,request.FILES)
        # check whether it's valid:
        if specimen_form.is_valid():
            #occ=specimen_form.save()
            occ = specimen_form.save(commit=False)
            #reference = form.save(commit=False)
            #occ.process_genus_name()
            occ.save()
                
            return HttpResponseRedirect('/siriuspasset/specimen_detail/'+str(occ.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        specimen_form = SpFossilSpecimenForm()
    return render(request, 'siriuspasset/specimen_form.html', {'specimen_form': specimen_form,'user_obj':user_obj})


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