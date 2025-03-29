
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
from authUser.models import VetProfile, PetOwnerProfile

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

@login_required
def process_refund(appointment):
    try:
        response = requests.post(
            f"{KHALTI_BASE_URL}/refund/",
            json={
                "pidx": appointment.pidx,
                "amount": appointment.amount_paid,
                "remarks": "Appointment rejected by vet"
            },
            headers={
                "Authorization": KHALTI_SECRET_KEY,
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        appointment.refund_id = data.get('refund_id')
        appointment.payment_status = 'refunded'
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Refund failed: {str(e)}")
        appointment.payment_status = 'refund_failed'
        return False

# Appointment Views
@login_required
def vet_list(request):
    vets = VetProfile.objects.all()
    return render(request, 'appointment/vet_list.html', {'vets': vets})

@login_required
def vet_schedule(request, vet_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedules = VetSchedule.objects.filter(vet=vet)
    return render(request, 'appointment/appointment_schedule.html', {
        'vet': vet,
        'schedules': schedules
    })

@login_required
def add_schedule(request):
    user = request.user
    vet = get_object_or_404(VetProfile, user=user)

    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        available = 'available' in request.POST

        VetSchedule.objects.create(
            pid=vet.pid,
            vet=vet,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            available=available
        )
        return redirect('appointment:vet_schedule', vet_id=vet.id)

    return render(request, 'appointment/appointment_creation_vets.html', {'vet': vet})

@login_required
def book_appointment(request, vet_id, schedule_id):
    vet = get_object_or_404(VetProfile, id=vet_id)
    schedule = get_object_or_404(VetSchedule, id=schedule_id)
    pet_owner = get_object_or_404(PetOwnerProfile, user=request.user)

    if Appointment.objects.filter(schedule=schedule, status="confirmed").exists():
        return render(request, "appointment/book_appt.html", {
            "vet": vet,
            "schedule": schedule,
            "error": "This slot is already booked."
        })

    if request.method == "POST":
        reason = request.POST.get("reason", "No reason provided")

        appointment = Appointment.objects.create(
            pet_owner=pet_owner,
            vet=vet,
            schedule=schedule,
            reason=reason,
            status="unpaid",
            payment_status='unpaid'
        )

        return redirect('appointment:initiate_khalti_payment', appointment_id=appointment.id)

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
    appointment.status = 'cancelled'
    appointment.save()
    return redirect('appointment:vet_list')

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

    if appointment.vet.user != request.user or appointment.status != "paid_pending_approval":
        return HttpResponseRedirect(reverse('appointment:vet_pending_appointments', args=[appointment.vet.id]))

    appointment.status = "confirmed"
    appointment.save()

    # Cancel other pending appointments for this slot
    Appointment.objects.filter(
        schedule=appointment.schedule
    ).exclude(id=appointment.id).update(status="cancelled")

    # Send confirmation to pet owner
    send_appointment_notification(
        appointment,
        "Appointment Confirmed",
        "appointment/confirmation_email.html"
    )

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
        # Process refund if payment was made
        if appointment.payment_status == 'paid' and appointment.pidx:
            try:
                # Step 1: Verify payment and get transaction details
                verify_response = requests.post(
                    f"{KHALTI_BASE_URL}/lookup/",
                    json={"pidx": appointment.pidx},
                    headers={
                        "Authorization": KHALTI_SECRET_KEY,
                        "Content-Type": "application/json",
                    },
                    timeout=10
                )
                verify_response.raise_for_status()
                verify_data = verify_response.json()
                
                if verify_data.get('status') != 'Completed' or not verify_data.get('transaction_id'):
                    raise Exception("Payment verification failed or missing transaction ID")

                transaction_id = verify_data['transaction_id']
                
                # Step 2: Process refund using Merchant API with proper authentication
                refund_url = f"https://dev.khalti.com/api/v2/merchant-transaction/{transaction_id}/refund/"
                
                # Merchant API requires different authentication
                merchant_secret = KHALTI_SECRET_KEY # Get this from Khalti Merchant Dashboard
                
                refund_response = requests.post(
                    refund_url,
                    json={
                        "mobile": KHALTI_TEST_ID,  # Customer's registered mobile
                        "amount": appointment.amount_paid  # Full refund amount in paisa
                    },
                    headers={
                        "Authorization": f"Key {merchant_secret}",
                        "Content-Type": "application/json",
                    },
                    timeout=15
                )
                
                refund_response.raise_for_status()
                refund_data = refund_response.json()

                if refund_data.get('status') == 'success' or refund_data.get('detail') == 'Transaction refund successful.':
                    appointment.payment_status = 'refunded'
                    appointment.refund_id = refund_data.get('refund_id', '')
                    messages.success(request, "Appointment rejected and payment refunded successfully.")
                else:
                    raise Exception(f"Refund failed: {refund_data.get('message', 'Unknown error')}")
            
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response:
                    error_msg = f"{e.response.status_code}: {e.response.text}"
                raise Exception(f"Refund API error: {error_msg}")

        # Update appointment status
        appointment.status = "rejected"
        appointment.save()

        # Send rejection notification
        send_appointment_notification(
            appointment,
            "Appointment Rejected",
            "appointment/rejection_email.html",
            is_rejection=True
        )

    except Exception as e:
        if appointment.payment_status == 'paid':
            appointment.payment_status = 'refund_failed'
            appointment.save()
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
