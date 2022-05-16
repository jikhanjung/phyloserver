from django.urls import path
from dolfinrest import views

urlpatterns = [
    path('dolfinrest/', views.dolfinrest_list),
    path('dolfinrest/<str:md5>/', views.dolfinrest_detail),
    #path('dolfinrest/md5hash/<str:md5hash>/', views.dolfinrest_md5hash),
]