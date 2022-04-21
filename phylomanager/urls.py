from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('server_status/', views.server_status, name='server_status'),
    path('package_list/', views.package_list, name='package_list'),    
    path('package_detail/<int:package_id>', views.package_detail, name='package_detail'),    
    path('add_package/', views.add_package, name='add_package'),
    path('edit_package/<int:pk>/', views.edit_package, name='edit_package'),
    path('delete_package/<int:pk>/', views.delete_package, name='delete_package'),

    path('run_list/', views.run_list, name='run_list'),
    path('run_detail/<int:run_id>/', views.run_detail, name='run_detail'),
    path('add_run/', views.add_run, name='add_run'),
    path('edit_run/<int:pk>/', views.edit_run, name='edit_run'),
    path('delete_run/<int:pk>/', views.delete_run, name='delete_run'),

]