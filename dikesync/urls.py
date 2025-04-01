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
    path('changed-records/', views.get_changed_records, name='get-changed-records'),
    # Web views
    path('web/sync-events/', views.sync_event_list, name='sync-event-list'),
    path('web/sync-events/<str:event_id>/', views.sync_event_detail, name='sync-event-detail'),
    path('web/dike-records/', views.dike_record_list, name='dike-record-list'),
    path('web/dike-records/<int:record_id>/', views.dike_record_detail, name='dike-record-detail'),
    path('web/dike-records/<int:record_id>/edit/', views.dike_record_edit, name='dike-record-edit'),
] 