from django.shortcuts import render

# Create your views here.
def make_appointment(request):
    return render(request, "appointment/appointment_schedule.html")
