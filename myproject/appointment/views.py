
from django.contrib import messages
import uuid
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import VetProfile, VetSchedule, Appointment
from authUser.models import VetProfile, PetOwnerProfile, Pet
from datetime import datetime


# Khalti Configuration
KHALTI_SECRET_KEY = 'key 669c9d57a23f42edbd586629b54b0a25'
KHALTI_PUBLIC_KEY = 'key aa619b6a9ea94e4fa2cddd9eb1541d27'
KHALTI_BASE_URL = 'https://a.khalti.com/api/v2/epayment'

# Test Credentials
KHALTI_TEST_ID = '9800000001'
KHALTI_TEST_MPIN = '1111'
KHALTI_TEST_OTP = '987654'

def send_appointment_notification(appointment, subject, template, is_rejection=False):
    context = {
        'appointment': appointment,
        'amount': appointment.amount_paid / 100,  # Convert paisa to NPR
        'is_rejection': is_rejection
    }
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.pet_owner.user.email],
        html_message=html_message
    )

# Payment Views
@login_required
def initiate_khalti_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Standard amount for demo (1000 NPR in paisa)
    amount_in_paisa = 1000 * 100
    
    payload = {
        "return_url": f"http://127.0.0.1:8000/appointment/verify_khalti/{appointment_id}/",
        "website_url": 'http://127.0.0.1:8000/',
        "amount": amount_in_paisa,
        "purchase_order_id": str(appointment.id),
        "purchase_order_name": f"Vet Appointment - {appointment.vet.user.username}",
        "customer_info": {
            "name": request.user.username,
            "email": request.user.email,
            "phone": KHALTI_TEST_ID
        }
    }
    
    headers = {
        "Authorization": KHALTI_SECRET_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{KHALTI_BASE_URL}/initiate/",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return redirect(data['payment_url'])
        
    except requests.exceptions.RequestException as e:
        return render(request, 'appointment/payment_error.html', {
            'error': str(e),
            'appointment': appointment
        })

@login_required
@csrf_exempt
def verify_khalti_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    pidx = request.GET.get('pidx')
    
    if not pidx:
        return render(request, 'appointment/payment_error.html', {
            'error': 'Missing payment ID',
            'appointment': appointment
        })
    
    try:
        response = requests.post(
            f"{KHALTI_BASE_URL}/lookup/",
            json={"pidx": pidx},
            headers={
                "Authorization": KHALTI_SECRET_KEY,
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'Completed':
            appointment.status = 'unpaid'
            appointment.payment_status = 'failed'
            appointment.save()
            return redirect('appointment:payment_failed', appointment_id=appointment.id)
        
        # Payment successful - store details and await vet approval
        appointment.pidx = pidx
        appointment.amount_paid = data['total_amount']
        appointment.status = 'paid_pending_approval'
        appointment.payment_status = 'paid'
        appointment.save()
        
        # Notify vet
        send_appointment_notification(
            appointment,
            "New Appointment Request",
            "appointment/new_appointment_email.html"
        )
        
        return redirect('appointment:payment_success', appointment_id=appointment.id)
        
    except requests.exceptions.RequestException as e:
        return render(request, 'appointment/payment_error.html', {
            'error': str(e),
            'appointment': appointment
        })

# Appointment Views
@login_required
def vet_list(request):
    vets = VetProfile.objects.all()
    return render(request, 'appointment/vet_list.html', {'vets': vets})

@login_required
def vet_schedule(request, vet_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    
    # Get all schedules for this vet
    schedules = VetSchedule.objects.filter(vet=vet)
    
    # Define the order of days for sorting
    day_order = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
    }
    
    # Sort schedules by day of week first, then by start time
    sorted_schedules = sorted(schedules, key=lambda x: (day_order[x.day_of_week], x.start_time))
    
    days_with_schedules = []
    for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        days_with_schedules.append({
            'name': day,
            'schedules': [schedule for schedule in sorted_schedules if schedule.day_of_week == day]
        })
    
    return render(request, 'appointment/appointment_schedule.html', {
        'vet': vet,
        'days_with_schedules': days_with_schedules
    })



def edit_schedule(request, schedule_id):
    user = request.user
    vet = get_object_or_404(VetProfile, user=user)
    schedule = get_object_or_404(VetSchedule, id=schedule_id, vet=vet)
    
    if request.method == 'POST':
        # Check if this is a delete request
        if 'delete_schedule' in request.POST:
            schedule.delete()
            return redirect('appointment:vet_schedule', vet_id=vet.id)
        
        # Otherwise, process as an edit request
        day_of_week = request.POST.get('day_of_week')
        start_time = datetime.strptime(request.POST.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.POST.get('end_time'), '%H:%M').time()
        
        # Validate time range
        if start_time >= end_time:
            return render(request, 'appointment/edit_schedule.html', {
                'vet': vet,
                'schedule': schedule,
                'error': 'End time must be after start time.'
            })

        # Check for overlapping schedules (excluding the current schedule)
        overlapping_schedules = VetSchedule.objects.filter(
            vet=vet,
            day_of_week=day_of_week,
            available=True
        ).exclude(
            id=schedule_id  # Exclude the current schedule
        ).exclude(
            # Exclude schedules that don't overlap
            end_time__lte=start_time  # Existing ends before new starts
        ).exclude(
            start_time__gte=end_time  # Existing starts after new ends
        )

        if overlapping_schedules.exists():
            return render(request, 'appointment/edit_schedule.html', {
                'vet': vet,
                'schedule': schedule,
                'error': 'The schedule overlaps with an existing one. Please select a different time.'
            })

        # Update the schedule
        schedule.day_of_week = day_of_week
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.save()

        return redirect('appointment:vet_schedule', vet_id=vet.id)

    return render(request, 'appointment/edit_schedule.html', {
        'vet': vet,
        'schedule': schedule
    })



def add_schedule(request):
    user = request.user
    vet = get_object_or_404(VetProfile, user=user)

    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        start_time = datetime.strptime(request.POST.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.POST.get('end_time'), '%H:%M').time()
        
        # Validate time range
        if start_time >= end_time:
            return render(request, 'appointment/appointment_creation_vets.html', {
                'vet': vet,
                'error': 'End time must be after start time.'
            })

        # Check for overlapping schedules
        overlapping_schedules = VetSchedule.objects.filter(
            vet=vet,
            day_of_week=day_of_week,
            available=True  # Only check against other available schedules
        ).exclude(
            # Exclude schedules that don't overlap
            end_time__lte=start_time  # Existing ends before new starts
        ).exclude(
            start_time__gte=end_time  # Existing starts after new ends
        )

        if overlapping_schedules.exists():
            return render(request, 'appointment/appointment_creation_vets.html', {
                'vet': vet,
                'error': 'The schedule overlaps with an existing one. Please select a different time.'
            })

        # If no overlap, create the new schedule
        VetSchedule.objects.create(
            pid=vet.pid,
            vet=vet,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            available=True
        )

        return redirect('appointment:vet_schedule', vet_id=vet.id)

    return render(request, 'appointment/appointment_creation_vets.html', {'vet': vet})


@login_required
def book_appointment(request, vet_id, schedule_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedule = get_object_or_404(VetSchedule, id=schedule_id)
    pet_owner = get_object_or_404(PetOwnerProfile, user=request.user)
    pets = pet_owner.pets.all()  # Fetch all pets for the dropdown

    if Appointment.objects.filter(schedule=schedule, status="confirmed").exists():
        return render(request, "appointment/book_appt.html", {
            "vet": vet,
            "schedule": schedule,
            "pets": pets,
            "error": "This slot is already booked."
        })

    if request.method == "POST":
        pet_id = request.POST.get("pet")
        reason = request.POST.get("reason", "No reason provided")
        
        try:
            selected_pet = Pet.objects.get(id=pet_id, owner=pet_owner)
        except Pet.DoesNotExist:
            return render(request, "appointment/book_appt.html", {
                "vet": vet,
                "schedule": schedule,
                "pets": pets,
                "error": "Invalid pet selection."
            })

        appointment = Appointment.objects.create(
            pet_owner=pet_owner,
            vet=vet,
            schedule=schedule,
            pet=selected_pet,
            reason=reason,
            status="unpaid",
            payment_status='unpaid'
        )

        return redirect('appointment:initiate_khalti_payment', appointment_id=appointment.id)

    return render(request, "appointment/book_appt.html", {
        "vet": vet,
        "schedule": schedule,
        "pets": pets
    })

@login_required
def book_with_credit(request, vet_id, schedule_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedule = get_object_or_404(VetSchedule, id=schedule_id)
    pet_owner = get_object_or_404(PetOwnerProfile, user=request.user)
    pets = pet_owner.pets.all()  # Fetch all pets for the dropdown

    if request.method == "POST":
        reason = request.POST.get("reason", "No reason provided")
        pet_id = request.POST.get("pet")

        # Check if slot is already booked
        if Appointment.objects.filter(schedule=schedule, status="confirmed").exists():
            messages.error(request, "This slot is already booked.")
            return redirect('appointment:book_appointment', vet_id=vet_id, schedule_id=schedule_id)

        # Check if user has sufficient credit (1000 NPR in paisa)
        if pet_owner.credit_balance < 1000 * 100:
            messages.error(request, "Insufficient credit balance")
            return redirect('appointment:book_appointment', vet_id=vet_id, schedule_id=schedule_id)

        try:
            # Check if valid pet is selected
            selected_pet = Pet.objects.get(id=pet_id, owner=pet_owner)

            # Deduct from credit balance
            pet_owner.credit_balance -= 1000 * 100  # Deduct 1000 NPR
            pet_owner.save()

            # Create appointment
            appointment = Appointment.objects.create(
                pet_owner=pet_owner,
                vet=vet,
                schedule=schedule,
                pet=selected_pet,  # Assign the selected pet
                reason=reason,
                status="unpaid",
                payment_status='unpaid',
                amount_paid=1000 * 100  # 1000 NPR in paisa
            )

            # Payment successful - store details and await vet approval
            appointment.status = 'paid_pending_approval'
            appointment.payment_status = 'paid'
            appointment.save()

            # Send notification to vet
            send_appointment_notification(
                appointment,
                "New Appointment Booking",
                "appointment/new_appointment_email.html"
            )

            messages.success(request, "Appointment booked successfully using your credit balance!")
            return redirect('appointment:appointment_detail', appointment_id=appointment.id)

        except Pet.DoesNotExist:
            messages.error(request, "Invalid pet selection.")
            return redirect('appointment:book_appointment', vet_id=vet_id, schedule_id=schedule_id)
        except Exception as e:
            # Revert credit deduction if error occurs
            pet_owner.credit_balance += 1000 * 100
            pet_owner.save()
            messages.error(request, f"Error booking appointment: {str(e)}")
            return redirect('appointment:book_appointment', vet_id=vet_id, schedule_id=schedule_id)

    # Render the page with the pet selection dropdown
    return render(request, "appointment/book_appt.html", {
        "vet": vet,
        "schedule": schedule,
        "pets": pets
    })



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
    
    try:
        # Only process credit for paid appointments
        if appointment.payment_status == 'paid' and appointment.status in ['confirmed', 'paid_pending_approval']:
            # Calculate 80% refund (in paisa)
            refund_amount = int(appointment.amount_paid * 0.8)
            
            # Add credit to owner's account
            appointment.pet_owner.credit_balance += refund_amount
            appointment.pet_owner.save()
            
            # Update appointment
            appointment.status = 'cancelled'
            appointment.save()
            
            messages.success(request, f"Appointment cancelled. {refund_amount/100:.2f} NPR (80%) credited to your account.")
        else:
            # For unpaid appointments or invalid statuses
            appointment.status = 'cancelled'
            appointment.save()
            messages.warning(request, "Appointment cancelled (no refund applicable).")
    
    except Exception as e:
        messages.error(request, f"Error cancelling appointment: {str(e)}")
        return redirect('appointment:appointment_detail', appointment_id=appointment.id)
    
    return redirect('appointment:appointment_list')

@login_required
def vet_pending_appointments(request, vet_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    pending_appointments = Appointment.objects.filter(vet=vet, status="paid_pending_approval")
    return render(request, "appointment/vet_pending_appointments.html", {
        "pending_appointments": pending_appointments,
        "vet": vet
    })

@login_required
def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Check if the appointment belongs to the logged-in vet and if it's in the 'paid_pending_approval' status
    if appointment.vet.user != request.user or appointment.status != "paid_pending_approval":
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

    # Change the appointment status to 'confirmed'
    appointment.status = "confirmed"
    appointment.save()

    # Cancel other pending appointments for this slot
    Appointment.objects.filter(
        schedule=appointment.schedule
    ).exclude(id=appointment.id).update(status="cancelled")

    # Update the availability of the schedule to False (unavailable) after confirming the appointment
    appointment.schedule.available = False
    appointment.schedule.save()

    # Send confirmation to the pet owner
    send_appointment_notification(
        appointment,
        "Appointment Confirmed",
        "appointment/confirmation_email.html"
    )

    # Redirect to the vet's pending appointments page
    return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))


@login_required
def reject_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Check permissions
    if not hasattr(appointment, 'vet') or not hasattr(appointment.vet, 'user') or \
       request.user != appointment.vet.user or appointment.status != "paid_pending_approval":
        messages.error(request, "You don't have permission to reject this appointment.")
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

    try:
        # Add credit to pet owner's account if payment was made
        if appointment.status == "paid_pending_approval" and appointment.payment_status == 'paid':
            appointment.pet_owner.credit_balance += appointment.amount_paid
            appointment.pet_owner.save()
            messages.success(request, "Appointment rejected. Amount credited to user's account.")

        # Update appointment status
        appointment.status = "rejected"
        appointment.save()

        # Send rejection notification (unchanged)
        send_appointment_notification(
            appointment,
            "Appointment Rejected",
            "appointment/rejection_email.html",
            is_rejection=True
        )

    except Exception as e:
        messages.error(request, f"Error rejecting appointment: {str(e)}")
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

    return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

@login_required
def vet_accepted_appointments(request, vet_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    accepted_appointments = Appointment.objects.filter(vet=vet, status="confirmed")
    return render(request, "appointment/vet_accepted_appointments.html", {
        "accepted_appointments": accepted_appointments,
        "vet": vet
    })

@login_required
def mark_completed(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        appointment.status = "completed"
        appointment.save()
        appointment.schedule.available = True
        appointment.schedule.save()

    return redirect("appointment:vet_accepted_appointments", vet_id=appointment.vet.id)

# Payment Status Views
@login_required
def payment_success(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'appointment/payment_success.html', {
        'appointment': appointment
    })

@login_required
def payment_failed(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'appointment/payment_failed.html', {
        'appointment': appointment
    })




