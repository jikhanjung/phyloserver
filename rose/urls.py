from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('occ_list/', views.occ_list, name='occ_list'),
    path('occ_detail/<int:occ_id>/', views.occ_detail, name='occ_detail'),
    path('add_occurrence/', views.add_occurrence, name='add_occurrence'),
    path('edit_occurrence/<int:pk>/', views.edit_occurrence, name='edit_occurrence'),
    path('delete_occurrence/<int:pk>/', views.delete_occurrence, name='delete_occurrence'),
    path('occ_chart/', views.occ_chart, name='occ_chart'),
    path('occ_chart/<int:file_id>', views.occ_chart, name='occ_chart'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('file_list/', views.file_list, name='file_list'),
    path('file_detail/<int:file_id>/', views.file_detail, name='file_detail'),
]
