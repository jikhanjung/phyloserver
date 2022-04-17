# Create your views here.
#from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg
from django.template import loader
from django.shortcuts import get_object_or_404, render

from .forms import PhyloRunForm, PhyloPackageForm, PhyloModelForm, PhyloLegForm
from django.forms import modelformset_factory, inlineformset_factory


def index(request):
    return HttpResponse("Index page")

def run_list(request):
    latest_run_list = PhyloRun.objects.order_by('-start_datetime')[:20]
    #template = loader.get_template('phylomanager/index.html')
    context = {
        'latest_run_list': latest_run_list,
    }
    #return HttpResponse(template.render(context, request))
    return render(request, 'phylomanager/index.html', context)

def run_detail(request, run_id):
    run = get_object_or_404(PhyloRun, pk=run_id)
    return render(request, 'phylomanager/run_detail.html', {'run': run})

def add_run(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PhyloRunForm(request.POST)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)
        # check whether it's valid:
        #print( str(form.data['entry_date'] ))
        if form.is_valid():
            phylorun = form.save(commit=False)
            #specimen.created_by = user_obj.username
            phylorun.save()
            #print("specimen saved", specimen)
            phyloleg_formset = PhyloLegFormSet(request.POST, request.FILES, instance=phylorun )
            if phyloleg_formset.is_valid():
                pk = phylorun.id
                #print("photo_formset:", photo_formset)
                phyloleg_instances = phyloleg_formset.save(commit=False)
                #print("photo_instances:", photo_instances)
                for phyloleg in phyloleg_instances:
                    phyloleg.save()
            return HttpResponseRedirect('/phylomanager/run_detail/'+str(pk))
    # if a GET (or any other method) we'll create a blank form
    else:
        form = PhyloRunForm()
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm, extra=5)
        phyloleg_formset = PhyloLegFormSet(queryset=PhyloLeg.objects.none())

    return render(request, '/phylomanager/run_form.html', {'form': form,'phyloleg_formset':phyloleg_formset})

def package_list(request):
    package_list = PhyloPackage.objects.all()
    output = '<br/> '.join([p.package_name for p in package_list])
    return HttpResponse(output)

def package_detail(request, package_id):
    return HttpResponse("You're looking at package %s." % package_id)

def phylomodel_list(request):
    model_list = PhyloModel.objects.all()
    output = '<br/> '.join([p.model_name for p in model_list])
    return HttpResponse(output)

def phylomodel_detail(request, model_id):
    return HttpResponse("You're looking at model %s." % model_id)

