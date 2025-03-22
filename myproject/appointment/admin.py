from django.contrib import admin

from .models import VetSchedule, Appointment


admin.site.register(VetSchedule)
admin.site.register(Appointment)