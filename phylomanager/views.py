# Create your views here.
#from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg
from django.template import loader
from django.shortcuts import get_object_or_404, render

from .forms import PhyloRunForm, PhyloPackageForm, PhyloModelForm, PhyloLegForm
from django.forms import modelformset_factory, inlineformset_factory
from json import dumps

def index(request):
    return HttpResponseRedirect('run_list')

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
    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        run_form = PhyloRunForm(request.POST,request.FILES)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)
        # check whether it's valid:
        if run_form.is_valid():
            phylorun = run_form.save(commit=False)
            print(phylorun.datafile)
            #phylorun.run_status='Registered'
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
        run_form = PhyloRunForm()
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm, extra=1)
        leg_formset = PhyloLegFormSet(queryset=PhyloLeg.objects.none())
        package_list = PhyloPackage.objects.all()
        for p in package_list:
            data_json.append( [p.package_name, p.package_type] )

    return render(request, 'phylomanager/run_form.html', {'run_form': run_form,'leg_formset':leg_formset,'data_json':dumps(data_json)})

def edit_run(request,pk):
    print("edit run")
    data_json = []
    run = get_object_or_404(PhyloRun, pk=pk)
    leg_formset = run.leg_set.all().order_by('leg_sequence')

    if request.method == 'POST':
        print("method POST")
        # create a form instance and populate it with data from the request:
        run_form = PhyloRunForm(request.POST,request.FILES,instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)

        # check whether it's valid:
        if run_form.is_valid():
            print("run form valid")
            run = run_form.save(commit=False)
            run.save()
            leg_formset = PhyloLegFormSet(request.POST,request.FILES, instance=run)
            if leg_formset.is_valid():
                print("leg formset valid")
                leg_instances = leg_formset.save(commit=False)
                for leg in leg_instances:
                    #if leg.id and leg.datafile == '':
                    #    leg.delete()
                    #else:
                    leg.save()
            else:
                print(leg_formset)
            return HttpResponseRedirect('/phylomanager/run_detail/'+str(pk))
        else:
            print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        run_form = PhyloRunForm(instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm, extra=0)
        leg_formset = PhyloLegFormSet(instance=run)
        package_list = PhyloPackage.objects.all()
        for p in package_list:
            data_json.append( [p.package_name, p.package_type] )

    return render(request, 'phylomanager/run_form.html', {'run_form': run_form,'leg_formset':leg_formset,'data_json':dumps(data_json)})

def delete_run(request, pk):
    run = get_object_or_404(PhyloRun, pk=pk)
    run.delete()
    return HttpResponseRedirect('/phylomanager/run_list')

def package_list(request):
    package_list = PhyloPackage.objects.all()
    context = {
        'package_list': package_list,
    }
    return render(request, 'phylomanager/package_list.html', context)

def package_detail(request, package_id):
    package = get_object_or_404(PhyloPackage, pk=package_id)
    return render(request, 'phylomanager/package_detail.html', {'package': package})

def add_package(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        package_form = PhyloPackageForm(request.POST)
        # check whether it's valid:
        if package_form.is_valid():
            package = package_form.save()
            return HttpResponseRedirect('/phylomanager/package_detail/'+str(package.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        package_form = PhyloPackageForm()

    return render(request, 'phylomanager/package_form.html', {'package_form': package_form})

def edit_package(request, pk):
    package = get_object_or_404(PhyloPackage, pk=pk)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        package_form = PhyloPackageForm(request.POST,instance=package)

        # check whether it's valid:
        if package_form.is_valid():
            package = package_form.save()
            return HttpResponseRedirect('/phylomanager/package_detail/'+str(pk))

    # if a GET (or any other method) we'll create a blank form
    else:
        package_form = PhyloPackageForm(instance=package)

    return render(request, 'phylomanager/package_form.html', {'package_form': package_form})

def delete_package(request, pk):
    package = get_object_or_404(PhyloPackage, pk=pk)
    package.delete()
    return HttpResponseRedirect('/phylomanager/package_list')



def phylomodel_list(request):
    model_list = PhyloModel.objects.all()
    output = '<br/> '.join([p.model_name for p in model_list])
    return HttpResponse(output)

def phylomodel_detail(request, model_id):
    return HttpResponse("You're looking at model %s." % model_id)

def server_status(request):
    current_run_list = PhyloRun.objects.filter(run_status__exact='IP').order_by('-start_datetime')[:20]
    context = {
        'current_run_list': current_run_list,
    }
    return render(request, 'phylomanager/server_status.html', context)
