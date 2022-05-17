from django.urls import path
from dolfinrest import views

urlpatterns = [
    #path('', views.dolfinrest_list),
    #path('', views.index, name='index'),
    path('dolfinimage_list/', views.DolfinImageList.as_view()),
    path('dolfinimage_detail/<int:pk>/', views.DolfinImageDetail.as_view()),
    path('dolfinimage_detail_md5hash/<str:md5hash>/', views.dolfinimage_detail_md5hash),
    #path('dolfinrest/md5hash/<str:md5hash>/', views.dolfinrest_md5hash),
]