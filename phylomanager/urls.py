from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:run_id>/', views.run_detail, name='detail'),
    path('package_list/', views.package_list, name='package_list'),    
    path('package_detail/', views.package_detail, name='package_detail'),    
]