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
    context = {
        'latest_run_list': latest_run_list,
    }
    return render(request, 'phylomanager/run_list.html', context)

def run_detail(request, run_id):
    run = get_object_or_404(PhyloRun, pk=run_id)
    return render(request, 'phylomanager/run_detail.html', {'run': run})

def add_run(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PhyloRunForm(request.POST)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)
        # check whether it's valid:
        if form.is_valid():
            phylorun = form.save(commit=False)
            phylorun.save()
            pk=phylorun.id
            phyloleg_formset = PhyloLegFormSet(request.POST, request.FILES, instance=phylorun )
            #print(phyloleg_formset)
            if phyloleg_formset.is_valid():
                phyloleg_instances = phyloleg_formset.save(commit=False)
                for phyloleg in phyloleg_instances:
                    phyloleg.save()
            else:
                print("phyloleg_formset is not valid")
                print(phyloleg_formset)
                
                #pass
            return HttpResponseRedirect('/phylomanager/run_detail/'+str(pk))
    # if a GET (or any other method) we'll create a blank form
    else:
        form = PhyloRunForm()
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm, extra=1)
        leg_formset = PhyloLegFormSet(queryset=PhyloLeg.objects.none())

    return render(request, 'phylomanager/run_form.html', {'form': form,'leg_formset':leg_formset})

def edit_run(request,pk):
    run = get_object_or_404(PhyloRun, pk=pk)
    legs = run.leg_set.all().order_by('leg_sequence')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PhyloRunForm(request.POST,instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)

        # check whether it's valid:
        if form.is_valid():
            run = form.save(commit=False)
            run.save()
            leg_formset = PhyloLegFormSet(request.POST, instance=run)
            if leg_formset.is_valid():
                leg_instances = leg_formset.save(commit=False)
                for leg in leg_instances:
                    if leg.id and leg.data == '':
                        leg.delete()
                    else:
                        leg.save()
            return HttpResponseRedirect('/phylomanager/run_detail/'+str(pk))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PhyloRunForm(instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)
        leg_formset = PhyloLegFormSet(instance=run)

    return render(request, 'phylomanager/run_form.html', {'form': form,'leg_formset':leg_formset})

def delete_run(request):    
    return

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

