from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('run_list/', views.run_list, name='run_list'),
    path('run_detail/<int:run_id>/', views.run_detail, name='run_detail'),
    path('package_list/', views.package_list, name='package_list'),    
    path('package_detail/<int:package_id>', views.package_detail, name='package_detail'),    
]