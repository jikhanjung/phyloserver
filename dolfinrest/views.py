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


from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer


@api_view(['GET', 'POST'])
def dolfinimage_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        snippets = DolfinImage.objects.all()
        serializer = DolfinImageSerializer(snippets, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DolfinImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#class DolfinImageViewSet(viewsets.ModelViewSet):
#    queryset = DolfinImage.objects.all()
#    serializer_class = DolfinImageSerializer

@csrf_exempt
def dolfinimage_list_old(request):
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

@csrf_exempt
def dolfinimage_detail_old(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        snippet = DolfinImage.objects.get(pk=pk)
    except DolfinImage.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = DolfinImageSerializer(snippet)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = DolfinImageSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        snippet.delete()
        return HttpResponse(status=204)

@csrf_exempt
def dolfinimage_detail_md5hash_old(request, md5hash):
    """
    Retrieve, update or delete a dolfin image.
    """
    try:
        snippet = DolfinImage.objects.get(md5hash=md5hash)
    except DolfinImage.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = DolfinImageSerializer(snippet)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = DolfinImageSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        snippet.delete()
        return HttpResponse(status=204)

@api_view(['GET', 'PUT', 'DELETE'])
def dolfinimage_detail(request, pk):
    """
    Retrieve, update or delete a dolfin image.
    """
    try:
        snippet = DolfinImage.objects.get(pk=pk)
    except DolfinImage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DolfinImageSerializer(snippet)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DolfinImageSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'PUT', 'DELETE'])
def dolfinimage_detail_md5hash(request, md5hash):
    """
    Retrieve, update or delete a dolfin image.
    """
    try:
        snippet = DolfinImage.objects.get(md5hash=md5hash)
    except DolfinImage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = DolfinImageSerializer(snippet)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DolfinImageSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

from .models import DolfinImage
from .serializers import DolfinImageSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class DolfinImageList(APIView):
    """
    List all snippets, or create a new snippet.
    """
    def get(self, request, format=None):
        snippets = DolfinImage.objects.all()
        serializer = DolfinImageSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DolfinImageSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        

class DolfinImageDetail(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """
    def get_object(self, pk):
        try:
            return DolfinImage.objects.get(pk=pk)
        except DolfinImage.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = DolfinImageSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = DolfinImageSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)