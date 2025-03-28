from django.db import models
import uuid

class DikeRecord(models.Model):
    symbol = models.CharField(max_length=200, null=True)
    stratum = models.CharField(max_length=200, null=True)
    rock_type = models.CharField(max_length=200, null=True)
    era = models.CharField(max_length=200, null=True)
    map_sheet = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=200, null=True)
    distance = models.FloatField(null=True)
    angle = models.FloatField(null=True)
    x_coord_1 = models.FloatField(null=True)
    y_coord_1 = models.FloatField(null=True)
    lat_1 = models.FloatField(null=True)
    lng_1 = models.FloatField(null=True)
    x_coord_2 = models.FloatField(null=True)
    y_coord_2 = models.FloatField(null=True)
    lat_2 = models.FloatField(null=True)
    lng_2 = models.FloatField(null=True)
    memo = models.TextField(null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DikeRecord {self.id} - {self.symbol or 'No Symbol'}"

class SyncEvent(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    event_id = models.CharField(max_length=200, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True)

    def __str__(self):
        return f"SyncEvent {self.event_id} - {self.status}"

    @classmethod
    def create_new_event(cls):
        event_id = str(uuid.uuid4())
        return cls.objects.create(event_id=event_id)

class SyncEventRecord(models.Model):
    SYNC_RESULT_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    sync_event = models.ForeignKey(SyncEvent, on_delete=models.CASCADE, related_name='records')
    dike_record = models.ForeignKey(DikeRecord, on_delete=models.CASCADE, related_name='sync_records')
    sync_result = models.CharField(max_length=20, choices=SYNC_RESULT_CHOICES)
    result_message = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sync_event', 'dike_record')

    def __str__(self):
        return f"SyncEventRecord {self.id} - {self.sync_result}"
