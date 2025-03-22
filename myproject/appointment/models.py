from django.db import models

import shortuuid
from shortuuid.django_fields import ShortUUIDField
from authUser.models import VetProfile, PetOwnerProfile

# Create your models here.

DAYS_OF_WEEK = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
]

class VetSchedule(models.Model):
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    vet = models.ForeignKey(VetProfile, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK, default="Monday")
    start_time = models.TimeField()
    end_time = models.TimeField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vet.user.full_name}:{self.day_of_week} ({self.start_time} - {self.end_time})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    pet_owner = models.ForeignKey(PetOwnerProfile, on_delete=models.CASCADE, related_name="appointments")
    vet = models.ForeignKey(VetProfile, on_delete=models.CASCADE, related_name="appointments")
    schedule = models.ForeignKey(VetSchedule, on_delete=models.CASCADE, related_name="appointments")
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.pet_owner.user.full_name} - {self.vet.user.full_name} {self.schedule.start_time} - {self.schedule.end_time})"
