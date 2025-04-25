from django.test import TestCase, RequestFactory, Client
from django.contrib.messages import get_messages
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from .models import User, VetProfile, PetOwnerProfile, Review, Pet
from appointment.models import Appointment, VetSchedule
from django.contrib import messages

User = get_user_model()

class ReviewVetTestCase(TestCase):
    def setUp(self):
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

        # Create owner user and profile
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
            start_time='09:00:00',
            end_time='12:00:00',
            available=True
        )

        # Create completed and paid appointment
        self.appointment = Appointment.objects.create(
            pet_owner=self.pet_owner,
            vet=self.vet_profile,
            schedule=self.schedule,
            status='completed',
            payment_status='paid',
            pet=self.pet,
            amount_paid=100 * 100  # 1000 NPR in paisa
        )

    def test_review_vet_unauthorized_user(self):
        """Test that only the pet owner can review the appointment"""
        # Create another user who didn't make the appointment
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True 
        )
        self.client.force_login(other_user)
        
        url = reverse('authUser:review_vet', args=[self.appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_review_vet_not_completed_appointment(self):
        """Test that only completed appointments can be reviewed"""
        # Change appointment status to pending
        self.appointment.status = 'paid_pending_approval'
        self.appointment.save()
        
        self.client.force_login(self.owner_user)
        url = reverse('authUser:review_vet', args=[self.appointment.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('appointment:appointment_detail', args=[self.appointment.id]))
        
        # Check for error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("You can only review completed and paid appointments", str(messages_list[0]))

    def test_review_vet_already_reviewed(self):
        """Test that a user can't review the same appointment twice"""
        # Create existing review
        Review.objects.create(
            vet=self.vet_profile,
            reviewer=self.owner_user,
            rating=5,
            comment='Great!',
            appointment=self.appointment
        )
        
        self.client.force_login(self.owner_user)
        url = reverse('authUser:review_vet', args=[self.appointment.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, reverse('appointment:appointment_detail', args=[self.appointment.id]))
        
        # Check for info message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("You have already reviewed this appointment", str(messages_list[0]))

    def test_review_vet_successful_submission(self):
        """Test successful review submission"""
        self.client.force_login(self.owner_user)
        url = reverse('authUser:review_vet', args=[self.appointment.id])
        
        data = {
            'rating': 5,
            'comment': 'Excellent service!'
        }
        
        response = self.client.post(url, data)
        
        # Check if review was created
        self.assertTrue(Review.objects.filter(appointment=self.appointment).exists())
        
        # Check redirect
        self.assertRedirects(response, reverse('appointment:appointment_detail', args=[self.appointment.id]))
        
        # Check success message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("Thank you for your review", str(messages_list[0]))

    def test_review_vet_template_used(self):
        """Test that the correct template is used for GET request"""
        self.client.force_login(self.owner_user)
        url = reverse('authUser:review_vet', args=[self.appointment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/review_vet.html')
        self.assertEqual(response.context['appointment'], self.appointment)

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('authUser:loginUser')
        self.register_url = reverse('authUser:register')
        
        # Create test user with complete profile
        self.valid_user = User.objects.create_user(
            email='rebof@gmail.com',
            username='rebofkatwal',
            password='testkatwal123',
            full_name='Rebof Katwal',
            profile_completed=True,
            status_verification=True 
        )

    def test_login_view_get(self):
        """Test 1: Verify login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authUser/register.html')

    def test_successful_login(self):
        """Test 2: Verify successful login with correct credentials"""
        response = self.client.post(self.login_url, {
            'email': 'rebof@gmail.com',
            'password': 'testkatwal123'
        }, follow=True)
        
        self.assertTemplateUsed(response, 'coreFunctions/index.html')
        

    def test_invalid_credentials(self):
        """Test 3: Verify error handling for wrong password"""
        response = self.client.post(self.login_url, {
            'email': 'rebof@gmail.com',
            'password': 'wrongpassword'
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Invalid username or password", [str(m) for m in messages])
        self.assertTemplateUsed(response, 'authUser/register.html')

    def test_incomplete_profile_redirect(self):
        """Test 4: Verify redirect for users with incomplete profiles"""
        incomplete_user = User.objects.create_user(
            email='incomplete@gmail.com',
            username='incomplete',
            password='testkatwal123',
            full_name='Incomplete User',
            profile_completed=False
        )
        response = self.client.post(self.login_url, {
            'email': 'incomplete@gmail.com',
            'password': 'testkatwal123'
        }, follow=True)
        self.assertTemplateUsed(response, 'authUser/profile.html')


    def test_already_authenticated_redirect(self):
        """Test 5: Verify redirect for already authenticated users"""
        self.client.force_login(self.valid_user)
        response = self.client.get(self.login_url, follow=True)
        # Should redirect to index page
        self.assertRedirects(response, reverse('coreFunctions:index'))

class RegisterViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.register_url = reverse('authUser:register')
        self.valid_data = {
            'full_name': 'Test User',
            'email': 'rebof@example.com',
            'username': 'testuser',
            'phone': '1234567890',
            'gender': 'male',
            'user_type': 'pet_owner',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }

    def test_register_view_get(self):
        '''renders the proper template'''
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authUser/register.html')

    def test_successful_pet_owner_registration(self):
        '''registration checking for pet owner'''
        response = self.client.post(self.register_url, data=self.valid_data)
        self.assertEqual(response.status_code, 302)
        
        # Check redirection
        self.assertRedirects(response, reverse('complete-profile'))
        
        # Check user creation
        user = User.objects.get(email='rebof@example.com')
        self.assertEqual(user.full_name, 'Test User')
        self.assertEqual(user.user_type, 'pet_owner')
        
        # Check profile creation
        self.assertTrue(PetOwnerProfile.objects.filter(user=user).exists())

         # Check OTP email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(user.otp), mail.outbox[0].body)
    
    # Check messages - now looking at both messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "An OTP has been sent to your email. Please verify to proceed.")
        self.assertEqual(str(messages[1]), "Hi Test User, your account was created successfully.")

    def test_successful_vet_registration(self):
        '''registration checking for vet'''
        vet_data = self.valid_data.copy()
        vet_data.update({
            'user_type': 'vet',
            'email': 'vetrebof@example.com',
            'username': 'testvet'
        })
        
        response = self.client.post(self.register_url, data=vet_data)
        
        # Check vet profile creation
        user = User.objects.get(email='vetrebof@example.com')
        self.assertTrue(VetProfile.objects.filter(user=user).exists())

    def test_password_mismatch(self):
        '''testing the two passwords for a match'''
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'wrongpassword'
        
        response = self.client.post(self.register_url, data=invalid_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Passwords do not match.")

    def test_existing_email(self):
        '''checking the uniqueness of the email '''
        User.objects.create_user(
            email='existinguser@example.com',
            username='existinguser',
            password='testpass123'
        )
        
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'existinguser@example.com'
        
        response = self.client.post(self.register_url, data=invalid_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Email already exists.")