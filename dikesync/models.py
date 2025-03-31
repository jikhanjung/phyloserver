from django.db import models
import uuid
import time
import random
import string

def base62_encode(num):
    chars = string.digits + string.ascii_letters
    base = len(chars)
    result = ''
    while num > 0:
        num, rem = divmod(num, base)
        result = chars[rem] + result
    return result or '0'

def generate_sortable_id(length=10):
    t = int(time.time() * 1000)  # current time in ms
    r = random.randint(0, 9999)  # add randomness
    combined = int(f"{t}{r}")
    encoded = base62_encode(combined)
    return encoded.rjust(length, '0')  # pad for consistent length

class DikeRecord(models.Model):
    unique_id = models.CharField(max_length=10, unique=True, null=False)
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
    is_deleted = models.BooleanField(default=False)
    last_sync_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"DikeRecord {self.unique_id} - {self.symbol or 'No Symbol'}"

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = generate_sortable_id()
        super().save(*args, **kwargs)

class SyncEvent(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    event_id = models.CharField(max_length=200, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True)

    def __str__(self):
        return f"SyncEvent {self.event_id} - {self.status}"

    @classmethod
    def create_new_event(cls):
        event_id = str(uuid.uuid4())
        return cls.objects.create(event_id=event_id)

