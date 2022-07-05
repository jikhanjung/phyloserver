# Create your views here.
#from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from .models import PhyloRun, PhyloPackage, PhyloModel, PhyloLeg, PhyloRunner
from django.template import loader
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.core.paginator import Paginator

from .forms import PhyloRunForm, PhyloRunUploadFileForm, PhyloPackageForm, PhyloModelForm, PhyloLegForm, PhyloUserChangeForm, PhyloUserRegisterForm
from django.forms import modelformset_factory, inlineformset_factory
from json import dumps
import platform, psutil
import io, os, zipfile
import tempfile

from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .utils import PhyloDatafile, PhyloTreefile
from Bio import Phylo
import matplotlib.pyplot as plt

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
    return HttpResponseRedirect('run_list')

def run_list(request):
    user_obj = get_user_obj(request)

    run_list = PhyloRun.objects.order_by('-created_datetime')
    paginator = Paginator(run_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'run_list': run_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'phylomanager/run_list.html', context)

def run_detail(request, run_id):
    user_obj = get_user_obj(request)

    run = get_object_or_404(PhyloRun, pk=run_id)
    phylodata = run.phylodata
    #print("phylodata:", phylodata)
    return render(request, 'phylomanager/run_detail.html', {'run': run, 'phylodata': phylodata, 'user_obj':user_obj})


def add_run_upload_file(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        run_form = PhyloRunUploadFileForm(request.POST,request.FILES)
        # check whether it's valid:
        if run_form.is_valid():
            phylorun = run_form.save(commit=False)
            #print(phylorun.datafile)
            phylorun.run_by_user = user_obj
            #phylorun.run_status='Registered'
            datafile_name = str(phylorun.datafile)
            if not phylorun.run_title:
                fname,fext = os.path.splitext(datafile_name)
                phylorun.run_title = fname
            phylorun.save()
            pk = phylorun.id
            phylorun.process_datafile()
            #print(phylorun.datafile)
            phylorun.phylodata.pre_save()
            phylorun.phylodata.save()
            #phylorun.phylodata = phylorun.phylodata
            phylorun.save()
            return HttpResponseRedirect('/phylomanager/edit_run/'+str(phylorun.id))
    # if a GET (or any other method) we'll create a blank form
    else:
        run_form = PhyloRunForm()

    return render(request, 'phylomanager/run_form_upload_file.html', {'run_form': run_form,'user_obj':user_obj})

def show_datamatrix(request,run_id):
    user_obj = get_user_obj(request)

    run = get_object_or_404(PhyloRun, pk=run_id)
    phylodata = run.phylodata

    return render(request, 'phylomanager/show_datamatrix.html', {'phylodata': phylodata,'user_obj':user_obj})


def add_run(request):
    user_obj = get_user_obj(request)

    data_json = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        run_form = PhyloRunForm(request.POST,request.FILES)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)
        # check whether it's valid:
        if run_form.is_valid():
            phylorun = run_form.save(commit=False)
            #print(phylorun.datafile)
            phylorun.run_by_user = user_obj
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

    return render(request, 'phylomanager/run_form.html', {'run_form': run_form,'leg_formset':leg_formset,'data_json':dumps(data_json),'user_obj':user_obj})

def edit_run(request,pk):
    user_obj = get_user_obj(request)

    #print("edit run")
    data_json = []
    run = get_object_or_404(PhyloRun, pk=pk)
    phylodata = run.phylodata
    leg_formset = run.leg_set.all().order_by('leg_sequence')

    if request.method == 'POST':
        #print("method POST")
        # create a form instance and populate it with data from the request:
        run_form = PhyloRunForm(request.POST,request.FILES,instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm)

        # check whether it's valid:
        if run_form.is_valid():
            #print("run form valid")
            run = run_form.save(commit=False)
            run.save()
            leg_formset = PhyloLegFormSet(request.POST,request.FILES, instance=run)
            if leg_formset.is_valid():
                #print("leg formset valid")
                leg_instances = leg_formset.save(commit=False)
                for leg in leg_instances:
                    if leg.leg_status == 'QD':
                        leg.run.run_status = 'QD'
                        leg.run.save()
                    #if leg.id and leg.datafile == '':
                    #    leg.delete()
                    #else:
                    leg.save()
            else:
                #print(leg_formset)
                pass
            return HttpResponseRedirect('/phylomanager/run_detail/'+str(pk))
        else:
            pass
            #print(run_form)

    # if a GET (or any other method) we'll create a blank form
    else:
        run_form = PhyloRunForm(instance=run)
        PhyloLegFormSet = inlineformset_factory(PhyloRun, PhyloLeg, form=PhyloLegForm, extra=1)
        leg_formset = PhyloLegFormSet(instance=run)
        package_list = PhyloPackage.objects.all()
        for p in package_list:
            data_json.append( [p.package_name, p.package_type] )

    return render(request, 'phylomanager/run_form.html', {'run_form': run_form,'phylodata':phylodata,'leg_formset':leg_formset,'data_json':dumps(data_json),'user_obj':user_obj})

def delete_run(request, pk):
    user_obj = get_user_obj(request)

    run = get_object_or_404(PhyloRun, pk=pk)
    run.delete()
    return HttpResponseRedirect('/phylomanager/run_list')

def package_list(request):
    if request.user.is_authenticated:
        user_obj = request.user
        user_obj.groupname_list = []
        for g in request.user.groups.all():
            user_obj.groupname_list.append(g.name)
    else:
        user_obj = None

    package_list = PhyloPackage.objects.all()
    context = {
        'package_list': package_list,
        'user_obj': user_obj
    }
    return render(request, 'phylomanager/package_list.html', context)

def package_detail(request, package_id):
    user_obj = get_user_obj(request)
    
    package = get_object_or_404(PhyloPackage, pk=package_id)
    return render(request, 'phylomanager/package_detail.html', {'package': package, 'user_obj':user_obj})

def add_package(request):
    user_obj = get_user_obj(request)

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

    return render(request, 'phylomanager/package_form.html', {'package_form': package_form, 'user_obj':user_obj})

def edit_package(request, pk):
    user_obj = get_user_obj(request)

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

    return render(request, 'phylomanager/package_form.html', {'package_form': package_form, 'user_obj':user_obj})

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

def download_run_result(request,pk):
    run = get_object_or_404(PhyloRun, pk=pk)
    #return HttpResponse("You're downloading run id %s." % pk)

    buffer = io.BytesIO()

    run_dirname = os.path.split( run.run_directory )[1]

    run_abspath = os.path.join( settings.MEDIA_ROOT, run.run_directory )

    #new_file = os.path.join( run_abspath, "leg_"+str(leg.id) + '.zip' )
    # creating zip file with write mode
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    # Walk through the files in a directory
    for dir_path, dir_names, files in os.walk(run_abspath):
        
        f_path = dir_path.replace(dir_path, '')
        f_path = f_path and f_path + os.sep
        print( dir_path, dir_names, files, f_path )
        # Writing each file into the zip
        leg_dirname = os.path.split(dir_path)[1]
        for file in files:
            print( dir_path, dir_names, file, f_path )
            zip.write(os.path.join(dir_path, file), os.path.join(leg_dirname,file))
    zip.close()
    buffer.seek(0)
    
    print("File Created successfully..")
    #return FileResponse(open(new_file,"rb"), as_attachment=True)
    return FileResponse(buffer, as_attachment=True, filename=run_dirname+".zip")

def show_tree(request,pk):
    leg = get_object_or_404(PhyloLeg, pk=pk)
    tree_filename = os.path.join(leg.leg_directory, "concensus_tree.svg")
    return FileResponse(open(tree_filename, 'rb'))    
    return FileResponse(buffer,filename=filename+".svg",)
    #return HttpResponse("You're downloading run id %s." % pk)


def download_leg_result(request,pk):
    leg = get_object_or_404(PhyloLeg, pk=pk)
    #return HttpResponse("You're downloading run id %s." % pk)

    buffer = io.BytesIO()
    run = leg.run

    run_abspath = os.path.join( settings.MEDIA_ROOT, run.run_directory )
    leg_dirname = "leg_"+str(leg.id)
    leg_directory = os.path.join( run_abspath, leg_dirname )

    #new_file = os.path.join( run_abspath, "leg_"+str(leg.id) + '.zip' )
    # creating zip file with write mode
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    # Walk through the files in a directory
    for dir_path, dir_names, files in os.walk(leg_directory):
        
        f_path = dir_path.replace(dir_path, '')
        f_path = f_path and f_path + os.sep
        #print( dir_path, dir_names, files, f_path )
        # Writing each file into the zip
        for file in files:
            print( dir_path, dir_names, f_path, file )
            zip.write(os.path.join(dir_path, file), file)
    zip.close()
    buffer.seek(0)
    
    print("File Created successfully..")
    #return FileResponse(open(new_file,"rb"), as_attachment=True)
    return FileResponse(buffer, as_attachment=True, filename=leg_dirname+".zip")
    


def server_status(request):
    user_obj = get_user_obj(request)

    my_system = {}
    my_system['machine'] = platform.machine()
    my_system['version'] = platform.version()
    my_system['OS'] = platform.platform()
    my_system['system'] = platform.system()
    my_system['processor'] = platform.processor()

    # CPU frequencies
    my_cpu = {}
    my_cpu['physical_cores'] = psutil.cpu_count(logical=False)
    my_cpu['total_cores'] = psutil.cpu_count(logical=True)
    cpufreq = psutil.cpu_freq()
    my_cpu['max_freq'] = f"{cpufreq.max:.2f}Mhz"
    my_cpu['min_freq'] = f"{cpufreq.min:.2f}Mhz"
    my_cpu['curr_freq'] = f"{cpufreq.current:.2f}Mhz"

    my_cpu['total_cpu_usage'] = f"{psutil.cpu_percent()}%"

    current_run_list = PhyloRun.objects.filter(run_status__exact='IP').order_by('-start_datetime')[:20]
    context = {
        'current_run_list': current_run_list,
        'my_machine': my_system,
        'my_cpu': my_cpu,
        'user_obj': user_obj,
    }
    return render(request, 'phylomanager/server_status.html', context)

def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)

    return redirect(request.META.get('HTTP_REFERER'))


def user_logout(request):
    logout(request)
    return redirect(request.META.get('HTTP_REFERER'))

def password(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('/phylomanager/')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'phylomanager/change_password.html', {
        'user_obj':user_obj,'form': form
    })    

def user_info(request):
    user_obj = get_user_obj(request)

    #print(user_obj.username)
    return render(request, 'phylomanager/user_info.html', {'user_obj': user_obj} )

def user_form(request):
    user_obj = get_user_obj(request)

    if request.method == 'POST':
        form = PhyloUserChangeForm(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/phylomanager/user_info')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PhyloUserChangeForm(instance=user_obj)

    return render(request, 'phylomanager/user_changeform.html', {'form': form,'user_obj':user_obj})

def user_register(request):
    if request.method == 'POST':
        form = PhyloUserRegisterForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/phylomanager/user_info')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PhyloUserRegisterForm()

    return render(request, 'phylomanager/user_changeform.html', {'form': form})

def runner_list(request):
    user_obj = get_user_obj(request)

    runner_list = PhyloRunner.objects.order_by('-created_datetime')
    paginator = Paginator(runner_list, 25) # Show 25 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'runner_list': runner_list,
        'user_obj': user_obj,
        'page_obj': page_obj,
    }
    return render(request, 'phylomanager/runner_list.html', context)

def runner_detail(request, runner_id):
    user_obj = get_user_obj(request)

    runner = get_object_or_404(PhyloRunner, pk=runner_id)
    #print("phylodata:", phylodata)
    return render(request, 'phylomanager/runner_detail.html', {'runner': runner, 'user_obj':user_obj})

def delete_runner(request, pk):
    user_obj = get_user_obj(request)

    run = get_object_or_404(PhyloRunner, pk=pk)
    run.delete()
    return HttpResponseRedirect('/phylomanager/runner_list')
