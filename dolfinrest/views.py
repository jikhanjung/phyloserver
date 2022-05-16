from django.shortcuts import render

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import DolfinImage
from .serializers import DolfinImageSerializer

# Create your views here.
from rest_framework import viewsets
#from serializers import PersonSerializer
#from .models import Person


class DolfinImageViewSet(viewsets.ModelViewSet):
    queryset = DolfinImage.objects.all()
    serializer_class = DolfinImageSerializer

@csrf_exempt
def dolfinrest_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    print("eeasdf")
    if request.method == 'GET':
        snippets = DolfinImage.objects.all()
        serializer = DolfinImageSerializer(snippets, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = DolfinImageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
