from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .models import PhyloRun, PhyloPackage

def index(request):
    latest_run_list = PhyloRun.objects.order_by('-start_datetime')[:20]
    output = '<br/> '.join([r.run_title for r in latest_run_list])
    return HttpResponse(output)

def run_detail(request, run_id):
    return HttpResponse("You're looking at run %s." % run_id)

def package_list(request):
    package_list = PhyloPackage.objects.all()
    output = '<br/> '.join([p.package_name for p in package_list])
    return HttpResponse(output)

def package_detail(request, package_id):
    return HttpResponse("You're looking at package %s." % package_id)

