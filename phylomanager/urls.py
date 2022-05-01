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
    #path('data_detail/<int:run_id>/', views.run_detail, name='run_detail'),
    path('add_run_upload_file/', views.add_run_upload_file, name='add_run_upload_file'),
    path('add_run/', views.add_run, name='add_run'),
    path('edit_run/<int:pk>/', views.edit_run, name='edit_run'),
    path('delete_run/<int:pk>/', views.delete_run, name='delete_run'),
    path('download_run_result/<int:pk>/', views.download_run_result, name='download_run_result'),
    path('download_leg_result/<int:pk>/', views.download_leg_result, name='download_leg_result'),

    # user
    path('user_info/', views.user_info, name='user_info'),
    path('user_form/', views.user_form, name='user_form'),
    path('user_register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('password/', views.password, name='password')
]