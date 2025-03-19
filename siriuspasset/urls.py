from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show_table/', views.show_table, name='show_table'),
    path('specimen_list/', views.specimen_list, name='specimen_list'),
    #path('occ_detail/<int:occ_id>/', views.occ_detail, name='occ_detail'),
    path('specimen_detail/<int:specimen_id>/', views.specimen_detail, name='specimen_detail'),
    path('add_specimen/', views.add_specimen, name='add_specimen'),
    path('edit_specimen/<int:pk>', views.edit_specimen, name='edit_specimen'),
    path('delete_specimen/<int:pk>', views.delete_specimen, name='delete_specimen'),
    path('slab_detail/<int:slab_id>/', views.slab_detail, name='slab_detail'),
    path('add_slab/', views.add_slab, name='add_slab'),
    path('edit_slab/<int:pk>', views.edit_slab, name='edit_slab'),
    path('delete_slab/<int:pk>', views.delete_slab, name='delete_slab'),
    path('recent_activities/', views.recent_activities, name='recent_activities'),
    path('recent_photos/', views.recent_photos, name='recent_photos'),
    path('directory_scans/', views.directory_scan_list, name='directory_scan_list'),
    path('directory_scans/<int:scan_id>/', views.directory_scan_detail, name='directory_scan_detail'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
]