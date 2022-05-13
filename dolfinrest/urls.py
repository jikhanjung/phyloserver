from django.urls import path
from dolfinrest import views

urlpatterns = [
    path('dolfinrest/', views.dolfinrest_list),
    path('dolfinrest/<int:pk>/', views.dolfinrest_detail),
]