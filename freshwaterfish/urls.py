from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('occ_list/', views.occ_list, name='occ_list'),
    path('occ_detail/<int:occ_id>/', views.occ_detail, name='occ_detail'),
    path('add_occurrence/', views.add_occurrence, name='add_occurrence'),
    path('edit_occurrence/<int:pk>/', views.edit_occurrence, name='edit_occurrence'),
    path('delete_occurrence/<int:pk>/', views.delete_occurrence, name='delete_occurrence'),
]