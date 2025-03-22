

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import VetProfile, VetSchedule, Appointment
from authUser.models import VetProfile, PetOwnerProfile
from django.http import HttpResponseRedirect
from django.urls import reverse

def vet_list(request):
    vets = VetProfile.objects.all()  # Get all vets
    return render(request, 'appointment/vet_list.html', {'vets': vets})

def vet_schedule(request, vet_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedules = VetSchedule.objects.filter(vet=vet)  # Get the schedules for this vet

    return render(request, 'appointment/appointment_schedule.html', {
        'vet': vet,
        'schedules': schedules
    })


@login_required
def add_schedule(request):
    user = request.user
    vet = get_object_or_404(VetProfile, user=user)

    if request.method == 'POST':
        # Get the logged-in user's vet profile
        
        # Extract form data
        day_of_week = request.POST.get('day_of_week')  # Expecting a day name (e.g., "Monday")
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        available = 'available' in request.POST  # Checkbox value


        # Create the VetSchedule entry with auto-fetched `pid` and `vet`
        VetSchedule.objects.create(
            pid=vet.pid,  # Automatically set from VetProfile
            vet=vet,
            day_of_week=day_of_week,  # Store the day instead of the date
            start_time=start_time,
            end_time=end_time,
            available=available
        )

        return redirect('appointment:vet_schedule', vet_id=vet.id)

    
    return render(request, 'appointment/appointment_creation_vets.html', {'vet': vet})


@login_required
def book_appointment(request, vet_id, schedule_id):
    """ Allow multiple pending requests but prevent new bookings if one is confirmed """
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedule = get_object_or_404(VetSchedule, id=schedule_id)
    pet_owner = get_object_or_404(PetOwnerProfile, user=request.user)

    # Check if the schedule already has a confirmed appointment
    confirmed_appointment = Appointment.objects.filter(schedule=schedule, status="confirmed").exists()
    if confirmed_appointment:
        return render(request, "appointment/book_appt.html", {
            "vet": vet,
            "schedule": schedule,
            "error": "This slot is already booked."
        })

    # Allow booking if no confirmed appointment exists
    if request.method == "POST":
        reason = request.POST.get("reason", "No reason provided")

        # Create a pending appointment
        appointment = Appointment.objects.create(
            pet_owner=pet_owner,
            vet=vet,
            schedule=schedule,
            reason=reason,
            status="pending"
        )

        return redirect("appointment:appointment_detail", appointment_id=appointment.id)

    return render(request, "appointment/book_appt.html", {"vet": vet, "schedule": schedule})

@login_required
def appointment_list(request):
    appointments = Appointment.objects.filter(pet_owner__user=request.user)  
    return render(request, "appointment/appointment_list.html", {"appointments": appointments})

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    return render(request, "appointment/appointment_detail.html", {"appointment": appointment})

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # You can update the status to 'cancelled' or delete the appointment entirely
    appointment.status = 'cancelled'
    appointment.save()

    # Redirect to the pet owner's list of appointments or another page
    return redirect('appointment:vet_list')


@login_required
def vet_pending_appointments(request, vet_id):
    """ Show the pending appointment requests for the logged-in vet """
    vet = get_object_or_404(VetProfile, id=vet_id)
    
    # Fetch all pending appointments for this vet
    pending_appointments = Appointment.objects.filter(vet=vet, status="pending")
    
    return render(request, "appointment/vet_pending_appointments.html", {"pending_appointments": pending_appointments, "vet": vet})

@login_required
def accept_appointment(request, appointment_id):
    """ Accept an appointment and cancel all other pending ones for the same time slot """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Ensure only the vet can accept the appointment
    if appointment.vet.user != request.user:
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

    # Accept the appointment
    appointment.status = "confirmed"
    appointment.save()

    # Cancel all other pending appointments for this schedule
    Appointment.objects.filter(schedule=appointment.schedule, status="pending").update(status="cancelled")

    return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))


@login_required
def reject_appointment(request, appointment_id):
    """ Reject an appointment request and update its status to 'cancelled' """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Only allow vets to reject their own appointments
    if appointment.vet.user != request.user:
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))
    
    appointment.status = "cancelled"
    appointment.save()
    
    return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

@login_required
def vet_accepted_appointments(request, vet_id):
    """ Show the accepted appointments for the logged-in vet """
    vet = get_object_or_404(VetProfile, id=vet_id)
    
    # Fetch all confirmed appointments for this vet
    accepted_appointments = Appointment.objects.filter(vet=vet, status="confirmed")
    
    return render(request, "appointment/vet_accepted_appointments.html", {"accepted_appointments": accepted_appointments, "vet": vet})

@login_required
def mark_completed(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        appointment.status = "completed"
        appointment.save()

        # Open the slot by setting `available=True`
        appointment.schedule.available = True
        appointment.schedule.save()

    # Redirect back to the vet's accepted appointments page
    return redirect("appointment:vet_accepted_appointments", vet_id=appointment.vet.id)