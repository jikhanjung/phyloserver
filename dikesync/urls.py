from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sync-events', views.SyncEventViewSet)
router.register(r'dike-records', views.DikeRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('submit-dike-record/', views.submit_dike_record, name='submit-dike-record'),
    path('submit-dike-records/', views.submit_dike_records, name='submit-dike-records'),
    path('sync-status/<str:event_id>/', views.check_sync_status, name='check-sync-status'),
    # Web views
    path('web/sync-events/', views.sync_event_list, name='sync-event-list'),
    path('web/sync-events/<str:event_id>/', views.sync_event_detail, name='sync-event-detail'),
] 