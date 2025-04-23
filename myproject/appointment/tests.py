from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import time

import requests
from appointment.models import VetSchedule, Appointment
from authUser.models import User, VetProfile, PetOwnerProfile, Pet
from django.contrib.messages import get_messages
from appointment.views import accept_appointment
from unittest.mock import patch, Mock



User = get_user_model()


class KhaltiPaymentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create vet user
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create pet owner user
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.pet_owner = self.owner_user.petownerprofile
        
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=9
        )
        
        # Create schedule
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(10, 0)
        )
        
        # Create unpaid appointment
        self.appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='unpaid',
            payment_status='unpaid',
            pet=self.pet
        )

    @patch('appointment.views.requests.post')
    def test_initiate_khalti_payment_success(self, mock_post):
        """Test successful payment initiation"""
        mock_response = Mock()
        mock_response.json.return_value = {'payment_url': 'https://khalti.com/payment/test123'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:initiate_khalti_payment', args=[self.appointment.id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://khalti.com/payment/test123')

    @patch('appointment.views.requests.post')
    def test_initiate_khalti_payment_failure(self, mock_post):  
        """Test failed payment initiation"""
    # Mock the exception being raised
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
    
        self.client.force_login(self.owner_user)
        response = self.client.get(
        reverse('appointment:initiate_khalti_payment', args=[self.appointment.id])
    )
    
    # Should render error template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/payment_error.html')


    @patch('appointment.views.requests.post')
    @patch('appointment.views.send_appointment_notification')
    def test_verify_khalti_payment_success(self, mock_notify, mock_post):
        """Test successful payment verification"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'Completed',
            'total_amount': 1000 * 100,
            'pidx': 'test_pidx_123'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:verify_khalti_payment', args=[self.appointment.id]),
            {'pidx': 'test_pidx_123'}
        )
        
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'paid_pending_approval')
        self.assertEqual(response.status_code, 302)


    @patch('appointment.views.requests.post')
    def test_verify_khalti_payment_failed(self, mock_post):
        """Test failed payment verification"""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'Failed'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
    
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:verify_khalti_payment', args=[self.appointment.id]),
            {'pidx': 'test_pidx_123'}
        )
    
    # Should redirect to failure page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:payment_failed', args=[self.appointment.id])
        )
    
    # Verify appointment was updated
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'unpaid')
        self.assertEqual(self.appointment.payment_status, 'failed')

    @patch('appointment.views.requests.post')
    def test_verify_khalti_payment_error(self, mock_post):
        """Test error during verification"""
        mock_post.side_effect = requests.exceptions.RequestException("Verification Error")
        
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:verify_khalti_payment', args=[self.appointment.id]),
            {'pidx': 'test_pidx_123'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/payment_error.html')

    def test_verify_khalti_missing_pidx(self):
        """Test verification with missing pidx parameter"""
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:verify_khalti_payment', args=[self.appointment.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/payment_error.html')
        self.assertIn('We encountered an issue with your payment', response.content.decode())

class CancelAppointmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create vet user
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create pet owner user with initial credit
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.pet_owner = self.owner_user.petownerprofile
        self.pet_owner.credit_balance = 1000 * 100  # 1000 NPR in paisa
        self.pet_owner.save()
        
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=3
        )
        
        # Create schedule
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(10, 0),
            available=False
        )
        
        # Create different appointment types
        self.paid_confirmed_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='confirmed',
            payment_status='paid',
            pet=self.pet,
            amount_paid=1000 * 100  # 1000 NPR in paisa
        )
        
        self.paid_pending_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=800 * 100  # 800 NPR in paisa
        )
        

    def test_cancel_paid_confirmed_appointment(self):
        """Test cancelling a paid, confirmed appointment with 80% refund"""
        initial_balance = self.pet_owner.credit_balance
        
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse('appointment:cancel_appointment', args=[self.paid_confirmed_appointment.id])
        )
        
        # Refresh from DB
        self.paid_confirmed_appointment.refresh_from_db()
        self.pet_owner.refresh_from_db()
        
        # Check status changed
        self.assertEqual(self.paid_confirmed_appointment.status, 'cancelled')
        
        # Check credit was added (80% of 1000 = 800 NPR)
        expected_refund = int(1000 * 100 * 0.8)
        self.assertEqual(
            self.pet_owner.credit_balance,
            initial_balance + expected_refund
        )
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("800.00 NPR (80%) credited", str(messages[0]))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('appointment:appointment_list'))

    def test_cancel_paid_pending_appointment(self):
        """Test cancelling a paid but pending approval appointment"""
        initial_balance = self.pet_owner.credit_balance
        
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse('appointment:cancel_appointment', args=[self.paid_pending_appointment.id])
        )
        
        # Refresh from DB
        self.paid_pending_appointment.refresh_from_db()
        self.pet_owner.refresh_from_db()
        
        # Check status changed
        self.assertEqual(self.paid_pending_appointment.status, 'cancelled')
        
        # Check credit was added (80% of 800 = 640 NPR)
        expected_refund = int(800 * 100 * 0.8)
        self.assertEqual(
            self.pet_owner.credit_balance,
            initial_balance + expected_refund
        )
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("640.00 NPR (80%) credited", str(messages[0]))




    def test_get_request_does_nothing(self):
        """Test that GET requests don't cancel appointments"""
        self.client.force_login(self.owner_user)
        response = self.client.get(
            reverse('appointment:cancel_appointment', args=[self.paid_confirmed_appointment.id])
        )
        
        # Status should remain unchanged
        self.paid_confirmed_appointment.refresh_from_db()
        self.assertEqual(self.paid_confirmed_appointment.status, 'confirmed')
        
        # Should still redirect
        self.assertEqual(response.status_code, 302)

class MarkCompletedTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create vet user with profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create another vet user for negative testing
        self.other_vet_user = User.objects.create_user(
            email='othervet@example.com',
            username='othervet',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.other_vet_profile = self.other_vet_user.vetprofile
        
        # Create pet owner user
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.pet_owner = self.owner_user.petownerprofile
        
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=9
        )
        
        # Create schedule (initially unavailable)
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0),
            available=False  # Starts as unavailable
        )
        
        # Create confirmed appointment
        self.appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='confirmed',
            payment_status='paid',
            pet=self.pet
        )

    def test_successful_completion(self):
        """Test marking an appointment as completed"""
        # Verify initial state
        self.assertEqual(self.appointment.status, 'confirmed')
        self.assertFalse(self.schedule.available)
        
        self.client.force_login(self.vet_user)
        response = self.client.post(
            reverse('appointment:mark_completed', args=[self.appointment.id])
        )
        
        # Refresh from DB
        self.appointment.refresh_from_db()
        self.schedule.refresh_from_db()
        
        # Check status changed
        self.assertEqual(self.appointment.status, 'completed')
        
        # Check schedule is now available
        self.assertTrue(self.schedule.available)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_accepted_appointments', args=[self.vet_profile.id])
        )

    def test_get_request_does_nothing(self):
        """Test that GET requests don't change status"""
        self.client.force_login(self.vet_user)
        response = self.client.get(
            reverse('appointment:mark_completed', args=[self.appointment.id])
        )
        
        # Status should remain unchanged
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')
        
        # Should still redirect
        self.assertEqual(response.status_code, 302)

    def test_wrong_vet_cannot_complete(self):
        """Test that other vets can't mark appointments as completed"""
        self.client.force_login(self.other_vet_user)
        response = self.client.post(
            reverse('appointment:mark_completed', args=[self.appointment.id])
    )
    
    # Appointment should remain unchanged
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')
    
    # Should redirect to the correct appointment's vet accepted page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_accepted_appointments', args=[self.vet_profile.id])  # not other_vet_profile!
    )

    def test_unauthorized_user_redirected(self):
        """Test that non-logged-in users are redirected to login"""
        response = self.client.post(
            reverse('appointment:mark_completed', args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))


class RejectAppointmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()  # Use Client instead of RequestFactory for messages
        self.factory = RequestFactory()
        
        # Create vet user with profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create another vet user for negative testing
        self.other_vet_user = User.objects.create_user(
            email='othervet@example.com',
            username='othervet',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.other_vet_profile = self.other_vet_user.vetprofile
        
        # Create pet owner user with sufficient credit
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.pet_owner = self.owner_user.petownerprofile
        self.pet_owner.credit_balance = 1000 * 100  # 1k NPR in paisa
        self.pet_owner.save()
        
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=9
        )
        
        # Create schedules
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0),
            available=True
        )
        
        # Create paid appointment
        self.paid_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=500 * 100  # 500 NPR in paisa
        )
        

    @patch('appointment.views.send_appointment_notification')
    def test_successful_rejection_with_refund(self, mock_send_notification):
        """Test rejecting a paid appointment credits the owner's account"""
        initial_balance = self.pet_owner.credit_balance
        
        # Use Client instead of RequestFactory to support messages
        self.client.force_login(self.vet_user)
        response = self.client.get(
            reverse('appointment:reject_appointment', args=[self.paid_appointment.id])
        )
        
        # Refresh from DB
        self.paid_appointment.refresh_from_db()
        self.pet_owner.refresh_from_db()
        
        # Check status changed
        self.assertEqual(self.paid_appointment.status, 'rejected')
        
        # Check credit was added
        self.assertEqual(
            self.pet_owner.credit_balance, 
            initial_balance + self.paid_appointment.amount_paid
        )
        # Check notification sent
        mock_send_notification.assert_called_once_with(
            self.paid_appointment,
            "Appointment Rejected",
            "appointment/rejection_email.html",
            is_rejection=True
        )
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_pending_appointments', args=[self.vet_profile.id])
        )


    def test_rejection_by_wrong_vet(self):
        """Test that other vets can't reject the appointment"""
        self.client.force_login(self.other_vet_user)
        response = self.client.get(
        reverse('appointment:reject_appointment', args=[self.paid_appointment.id])
        )
    
    # Check appointment wasn't changed
        self.paid_appointment.refresh_from_db()
        self.assertEqual(self.paid_appointment.status, 'paid_pending_approval')
    
    # Check redirect to the correct appointment's vet pending page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_pending_appointments', args=[self.vet_profile.id])  # not other_vet_profile!
        )

    @patch('appointment.views.send_appointment_notification')
    def test_rejection_error_handling(self, mock_send_notification):
        """Test error during rejection is properly handled"""
        # Simulate an error in credit processing
        original_credit = self.pet_owner.credit_balance
        with patch.object(PetOwnerProfile, 'save', side_effect=Exception("Test error")):
            self.client.force_login(self.vet_user)
            response = self.client.get(
                reverse('appointment:reject_appointment', args=[self.paid_appointment.id])
            )
            
            # Check credit wasn't changed
            self.pet_owner.refresh_from_db()
            self.assertEqual(self.pet_owner.credit_balance, original_credit)
            
            # Check redirect
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url,
                reverse('appointment:vet_pending_appointments', args=[self.vet_profile.id])
            )

class AcceptAppointmentTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create vet user with profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create another vet user for negative testing
        self.other_vet_user = User.objects.create_user(
            email='othervet@example.com',
            username='othervet',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.other_vet_profile = self.other_vet_user.vetprofile
        
        # Create pet owner user with sufficient credit
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.pet_owner = self.owner_user.petownerprofile
        self.pet_owner.credit_balance = 1000 * 100  # 1k NPR in paisa
        self.pet_owner.save()
        
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=9
        )
        
        # Create schedules
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0),
            available=True
        )
        
        self.other_schedule = VetSchedule.objects.create(
            vet=self.other_vet_profile,
            day_of_week='Tuesday',
            start_time=time(10, 0),
            end_time=time(11, 0),
            available=True
        )
        
        # Create appointments
        self.appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=100 * 100  # 1000 NPR in paisa
        )
        
        self.other_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=100 * 100
        )
        
        self.different_vet_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.other_vet_profile,
            schedule=self.other_schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=100 * 100
        )
        

    @patch('appointment.views.send_appointment_notification')
    def test_accept_appointment_success(self, mock_send_notification):
        # Create request
        request = self.factory.get('/')
        request.user = self.vet_user
        
        # Call the view
        response = accept_appointment(request, self.appointment.id)
        
        # Refresh objects from db
        self.appointment.refresh_from_db()
        self.other_appointment.refresh_from_db()
        self.schedule.refresh_from_db()
        
        # Check appointment status changed
        self.assertEqual(self.appointment.status, 'confirmed')
        
        # Check other appointment was rejected
        self.assertEqual(self.other_appointment.status, 'rejected')
        
        # Check schedule is now unavailable
        self.assertFalse(self.schedule.available)
        
        # Check notifications were sent
        self.assertEqual(mock_send_notification.call_count, 2)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_pending_appointments', args=[self.vet_profile.id])
        )

    def test_accept_appointment_wrong_vet(self):
    # Create request with other vet user
        request = self.factory.get('/')
        request.user = self.other_vet_user

    # Call the view
        response = accept_appointment(request, self.appointment.id)

    # Check redirect is to the correct appointment's vet page, not current user
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('appointment:vet_pending_appointments', args=[self.vet_profile.id])
        )

    # Confirm status did not change
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'paid_pending_approval')

    @patch('appointment.views.send_appointment_notification')
    def test_accept_appointment_rejects_others(self, mock_send_notification):
        # Create another appointment for the same schedule
        another_appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='paid_pending_approval',
            payment_status='paid',
            pet=self.pet,
            amount_paid=500 * 100
        )
        
        # Create request
        request = self.factory.get('/')
        request.user = self.vet_user
        
        # Call the view
        response = accept_appointment(request, self.appointment.id)
        
        # Refresh objects
        another_appointment.refresh_from_db()
        
        # Check other appointment was rejected
        self.assertEqual(another_appointment.status, 'rejected')
        
        # Check notification was sent for rejection
        mock_send_notification.assert_any_call(
            another_appointment,
            "Appointment Rejected",
            "appointment/rejection_email.html",
            is_rejection=True
        )


class BookWithCreditTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create vet user and profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        # Create pet owner user with sufficient credit
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.pet_owner = self.owner_user.petownerprofile
        self.pet_owner.credit_balance = 1000 * 100  # 1k NPR in paisa
        self.pet_owner.save()
        self.pet = Pet.objects.create(  # Create pet
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=9
        )
        self.schedule = VetSchedule.objects.create(  # Create schedule
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        self.client.login(email='owner@example.com', password='testpass123') # Login the pet owner

    def test_successful_booking_with_credit(self):
        """Test successful booking with sufficient credit"""
        initial_credit = self.pet_owner.credit_balance
        
        response = self.client.post(
            reverse('appointment:book_with_credit', args=[self.vet_profile.id, self.schedule.id]),
            {
                'pet': str(self.pet.id),
                'reason': 'Annual checkup'
            },
            follow=True
        )
        
        # Check redirect to appointment detail
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/appointment_detail.html')
        
        # Verify appointment was created with correct status
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.status, 'paid_pending_approval')
        self.assertEqual(appointment.payment_status, 'paid')
        self.assertEqual(appointment.amount_paid, 1000 * 100)
        
        # Verify credit was deducted
        self.pet_owner.refresh_from_db()
        self.assertEqual(self.pet_owner.credit_balance, initial_credit - 1000 * 100)

    def test_insufficient_credit(self):
        """Test booking with insufficient credit"""
        # Set low credit balance
        self.pet_owner.credit_balance = 500 * 100  # 500 NPR
        self.pet_owner.save()
        
        response = self.client.post(
            reverse('appointment:book_with_credit', args=[self.vet_profile.id, self.schedule.id]),
            {
                'pet': str(self.pet.id),
                'reason': 'Checkup'
            },
            follow=True
        )
        
        # Should redirect back to booking page with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/book_appt.html')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Insufficient credit balance')
        
        # No appointment should be created
        self.assertEqual(Appointment.objects.count(), 0)


    def test_credit_rollback_on_error(self):
        """Test credit is rolled back if error occurs during booking"""
        initial_credit = self.pet_owner.credit_balance
        print(f"Initial credit balance: {initial_credit}")  # Debugging line

        # Force an error by providing invalid data
        response = self.client.post(
            reverse('appointment:book_with_credit', args=[self.vet_profile.id, self.schedule.id]),
        {
            'pet': 'invalid',  # Will cause error (invalid pet ID)
            'reason': 'Checkup'
        }
    )
        
        # Verify credit was not deducted
        self.pet_owner.refresh_from_db()
        print(f"Credit balance after error: {self.pet_owner.credit_balance}")  # Debugging line

        self.assertEqual(self.pet_owner.credit_balance, initial_credit)

class BookAppointmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create vet user and profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        # Create pet owner user and profile
        self.owner_user = User.objects.create_user(
            email='owner@example.com',
            username='petowner',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.pet_owner = self.owner_user.petownerprofile
        # Create pet
        self.pet = Pet.objects.create(
            owner=self.pet_owner,
            name='Fluffy',
            breed='Persian',
            species='Cat',
            age=4
        )
        # Create schedule
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        self.client.login(email='owner@example.com', password='testpass123') # Login the pet owner

    def test_book_appointment_get(self):
        """Test GET request to book appointment page"""
        response = self.client.get(reverse('appointment:book_appointment', args=[self.vet_profile.id, self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/book_appt.html')
        self.assertEqual(response.context['vet'], self.vet_profile)
        self.assertEqual(response.context['schedule'], self.schedule)
        self.assertIn(self.pet, response.context['pets'])


    def test_successful_booking(self):
        """Test successful appointment booking"""
        response = self.client.post(
        reverse('appointment:book_appointment', args=[self.vet_profile.id, self.schedule.id]),
        {
            'pet': str(self.pet.id),
            'reason': 'Annual checkup'
        }
    )
    
    # Verify we got a redirect response (302)
        self.assertEqual(response.status_code, 302)
    
    # Verify the redirect URL pattern
        appointment = Appointment.objects.first()
        expected_url = reverse('appointment:initiate_khalti_payment', kwargs={'appointment_id': appointment.id})
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
    
    # Verify appointment was created with correct data
        self.assertEqual(appointment.pet_owner, self.pet_owner)
        self.assertEqual(appointment.vet, self.vet_profile)
        self.assertEqual(appointment.pet, self.pet)
        self.assertEqual(appointment.status, 'unpaid')


    def test_missing_pet_selection(self):
        """Test booking without selecting a pet"""
        response = self.client.post(reverse('appointment:book_appointment', args=[self.vet_profile.id, self.schedule.id]), {
            'reason': 'Checkup'
            # Missing pet field
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please select a pet')
        self.assertEqual(Appointment.objects.count(), 0)


class EditScheduleTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create vet user and profile
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        self.vet_profile = self.vet_user.vetprofile
        
        # Create initial schedule
        self.schedule = VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Monday',
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        # Login the vet
        self.client.login(email='vet@example.com', password='testpass123')

    def test_edit_schedule_get(self):
        """Test GET request to edit schedule page"""
        response = self.client.get(reverse('appointment:edit_schedule', args=[self.schedule.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/edit_schedule.html')
        self.assertEqual(response.context['schedule'], self.schedule)

    def test_valid_schedule_update(self):
        """Test updating schedule with valid data"""
        response = self.client.post(reverse('appointment:edit_schedule', args=[self.schedule.id]), {
            'day_of_week': 'Tuesday',
            'start_time': '10:00',
            'end_time': '15:00'
        })
        
        self.assertRedirects(response, reverse('appointment:vet_schedule', kwargs={'vet_id': self.vet_profile.id}))
        
        # Refresh schedule from DB
        updated_schedule = VetSchedule.objects.get(pk=self.schedule.id)
        self.assertEqual(updated_schedule.day_of_week, 'Tuesday')
        self.assertEqual(updated_schedule.start_time, time(10, 0))
        self.assertEqual(updated_schedule.end_time, time(15, 0))

    def test_invalid_time_range(self):
        """Test updating with end time before start time"""
        response = self.client.post(reverse('appointment:edit_schedule', args=[self.schedule.id]), {
            'day_of_week': 'Wednesday',
            'start_time': '14:00',
            'end_time': '12:00'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End time must be after start time.')
        
        # Verify schedule wasn't updated
        unchanged_schedule = VetSchedule.objects.get(pk=self.schedule.id)
        self.assertEqual(unchanged_schedule.day_of_week, 'Monday')

    def test_overlapping_schedule(self):
        """Test updating with overlapping time"""
        # Create another schedule that would cause overlap
        VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Thursday',
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        
        response = self.client.post(reverse('appointment:edit_schedule', args=[self.schedule.id]), {
            'day_of_week': 'Thursday',  # Same day as existing schedule
            'start_time': '11:00',      # Overlaps with 10-12
            'end_time': '13:00'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The schedule overlaps with an existing one.')
        
        # Verify schedule wasn't updated
        unchanged_schedule = VetSchedule.objects.get(pk=self.schedule.id)
        self.assertEqual(unchanged_schedule.day_of_week, 'Monday')

    def test_schedule_deletion(self):
        """Test deleting a schedule"""
        response = self.client.post(reverse('appointment:edit_schedule', args=[self.schedule.id]), {
            'delete_schedule': 'true'
        })
        
        self.assertRedirects(response, reverse('appointment:vet_schedule', kwargs={'vet_id': self.vet_profile.id}))
        self.assertFalse(VetSchedule.objects.filter(pk=self.schedule.id).exists())


class AddScheduleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.vet_user = User.objects.create_user(
            email='vet@gmail.com',
            username='Dr_Katwal',
            password='test123',
            user_type='vet',
            profile_completed=True,
            status_verification=True 
        )
        # Get the vet profile created by the signal
        self.vet_profile = self.vet_user.vetprofile
        self.client.login(email='vet@gmail.com', password='test123')
        self.url = reverse('appointment:add_schedule')

    def test_successful_schedule_creation(self):
        """Test creating a valid schedule"""
        response = self.client.post(self.url, {
            'day_of_week': 'Monday',
            'start_time': '10:00',
            'end_time': '12:00',
        })
        self.assertRedirects(response, reverse('appointment:vet_schedule', kwargs={'vet_id': self.vet_profile.id}))
        self.assertTrue(VetSchedule.objects.filter(vet=self.vet_profile, day_of_week='Monday').exists())

    def test_schedule_end_time_before_start_time(self):
        """Test invalid time range (end before start)"""
        response = self.client.post(self.url, {
            'day_of_week': 'Tuesday',
            'start_time': '14:00',
            'end_time': '13:00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End time must be after start time.')

    def test_overlapping_schedule(self):
        """Test overlapping schedule detection"""
        # Create initial schedule
        VetSchedule.objects.create(
            vet=self.vet_profile,
            day_of_week='Wednesday',
            start_time=time(9, 0),
            end_time=time(11, 0),
            available=True
        )
        
        # Try to create overlapping schedule
        response = self.client.post(self.url, {
            'day_of_week': 'Wednesday',
            'start_time': '10:00',
            'end_time': '12:00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The schedule overlaps with an existing one.')