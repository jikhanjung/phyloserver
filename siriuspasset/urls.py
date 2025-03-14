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
]