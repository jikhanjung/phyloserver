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

    path('occ_list4/', views.occ_list4, name='occ_list4'),
    path('occ_detail4/<int:occ_id>/', views.occ_detail4, name='occ_detail4'),
    path('add_occurrence4/', views.add_occurrence4, name='add_occurrence4'),
    path('edit_occurrence4/<int:pk>/', views.edit_occurrence4, name='edit_occurrence4'),
    path('delete_occurrence4/<int:pk>/', views.delete_occurrence4, name='delete_occurrence4'),

    path('occ_list5/', views.occ_list5, name='occ_list5'),
    path('occ_detail5/<int:occ_id>/', views.occ_detail5, name='occ_detail5'),
    path('add_occurrence5/', views.add_occurrence5, name='add_occurrence5'),
    path('edit_occurrence5/<int:pk>/', views.edit_occurrence5, name='edit_occurrence5'),
    path('delete_occurrence5/<int:pk>/', views.delete_occurrence5, name='delete_occurrence5'),

    path('occ_list6/', views.occ_list6, name='occ_list6'),
    path('occ_detail6/<int:occ_id>/', views.occ_detail6, name='occ_detail6'),
    path('add_occurrence6/', views.add_occurrence6, name='add_occurrence6'),
    path('edit_occurrence6/<int:pk>/', views.edit_occurrence6, name='edit_occurrence6'),
    path('delete_occurrence6/<int:pk>/', views.delete_occurrence6, name='delete_occurrence6'),

    path('show_table/', views.show_table, name='show_table'),
    #path('show_table_by_genus/', views.show_table_by_genus, name='show_table_by_genus'),
    #path('show_cluster/', views.show_cluster, name='show_cluster'),
    path('download_cluster/', views.download_cluster, name='download_cluster'),

    path('locality_list/', views.locality_list, name='locality_list'),
    path('locality_detail/<int:pk>/', views.locality_detail, name='locality_detail'),
    path('add_locality/', views.add_locality, name='add_locality'),
    path('edit_locality/<int:pk>/', views.edit_locality, name='edit_locality'),
    path('delete_locality/<int:pk>/', views.delete_locality, name='delete_locality'),


    path('pbdb_list/', views.pbdb_list, name='pbdb_list'),
    path('pbdb_detail/<int:occ_id>/', views.pbdb_detail, name='pbdb_detail'),
    #path('add_occurrence/', views.add_occurrence, name='add_occurrence'),
    path('edit_pbdb/<int:pk>/', views.edit_pbdb, name='edit_pbdb'),
    #path('delete_pbdb/<int:pk>/', views.delete_occurrence, name='delete_occurrence'),

    path('combined_list/', views.combined_list, name='combined_list'),
    path('combined_detail/<int:occ_id>/', views.combined_detail, name='combined_detail'),
    path('show_combined_table/', views.show_combined_table, name='show_combined_table'),
    path('download_combined_cluster/', views.download_combined_cluster, name='download_combined_cluster'),

    # chronostrat unit urls
    path('chronounit_list/', views.chronounit_list, name='chronounit_list'),
    path('chronounit_chart/', views.chronounit_chart, name='chronounit_chart'),
    path('chronounit_list/<int:pk>/', views.chronounit_list, name='chronounit_list'),
    path('chronounit_detail/<int:pk>/', views.chronounit_detail, name='chronounit_detail'),
    path('chronounit_add/', views.chronounit_add, name='chronounit_add'),
    path('chronounit_edit/<int:pk>/', views.chronounit_edit, name='chronounit_edit'),
    path('chronounit_delete/<int:pk>/', views.chronounit_delete, name='chronounit_delete'),


    # NK data download
    path('nkdata_download/', views.nkdata_download, name='nkdata_download'),
    path('management_command/', views.management_command, name='management_command'),
] 