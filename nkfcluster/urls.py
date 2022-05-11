from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('occ_list/', views.occ_list, name='occ_list'),
    path('occ_detail/<int:occ_id>/', views.occ_detail, name='occ_detail'),
    path('add_occurrence/', views.add_occurrence, name='add_occurrence'),
    path('edit_occurrence/<int:pk>/', views.edit_occurrence, name='edit_occurrence'),
    path('delete_occurrence/<int:pk>/', views.delete_occurrence, name='delete_occurrence'),

    path('occ_list2/', views.occ_list2, name='occ_list2'),
    path('occ_detail2/<int:occ_id>/', views.occ_detail2, name='occ_detail2'),
    path('add_occurrence2/', views.add_occurrence2, name='add_occurrence2'),
    path('edit_occurrence2/<int:pk>/', views.edit_occurrence2, name='edit_occurrence2'),
    path('delete_occurrence2/<int:pk>/', views.delete_occurrence2, name='delete_occurrence2'),

    path('occ_list3/', views.occ_list3, name='occ_list3'),
    path('occ_detail3/<int:occ_id>/', views.occ_detail3, name='occ_detail3'),
    path('add_occurrence3/', views.add_occurrence3, name='add_occurrence3'),
    path('edit_occurrence3/<int:pk>/', views.edit_occurrence3, name='edit_occurrence3'),
    path('delete_occurrence3/<int:pk>/', views.delete_occurrence3, name='delete_occurrence3'),

    path('show_table/', views.show_table, name='show_table'),
    path('show_table_by_genus/', views.show_table_by_genus, name='show_table_by_genus'),
    path('show_cluster/', views.show_cluster, name='show_cluster'),
    path('download_cluster/', views.download_cluster, name='download_cluster'),
] 