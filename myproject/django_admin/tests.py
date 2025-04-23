
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.timezone import now
from authUser.models import VetProfile
from unittest.mock import patch
from django.contrib.auth import get_user_model


User = get_user_model()



class ApproveVetTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create admin user (must have is_staff=True)
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='testpass123',
            user_type='admin',
            profile_completed=True,
            status_verification=True,
            is_staff=True
        )
        
        # Create unverified vet user
        self.vet_user = User.objects.create_user(
            email='vet@example.com',
            username='vetuser',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=False,
            full_name='Dr. Vet User'
        )
        self.vet_profile = self.vet_user.vetprofile

    def test_approve_vet_success(self):
        """Test successful vet approval by admin"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:approve_vet', args=[self.vet_profile.id])
        )
        
        self.vet_user.refresh_from_db()
        self.vet_profile.refresh_from_db()
        
        self.assertTrue(self.vet_user.status_verification)
        self.assertTrue(self.vet_profile.verified)
        self.assertRedirects(response, reverse('django_admin:vet_approvals'))

    def test_approve_vet_unauthorized_redirect(self):
        """Test non-admin users are redirected to login"""
        # Create regular non-staff user
        regular_user = User.objects.create_user(
            email='user@example.com',
            username='regular',
            password='testpass123',
            user_type='pet_owner',
            is_staff=False,
            profile_completed=True,
            status_verification=True
        )
        
        self.client.force_login(regular_user)
        response = self.client.post(
            reverse('django_admin:approve_vet', args=[self.vet_profile.id]),
            follow=True  # Follow the redirect
        )
        
        # Should redirect to admin login
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Check vet was not approved
        self.vet_user.refresh_from_db()
        self.assertFalse(self.vet_user.status_verification)

    def test_approve_vet_unauthenticated_redirect(self):
        """Test unauthenticated users are redirected to login"""
        response = self.client.post(
            reverse('django_admin:approve_vet', args=[self.vet_profile.id]),
            follow=True
        )
        
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Check vet was not approved
        self.vet_user.refresh_from_db()
        self.assertFalse(self.vet_user.status_verification)



class AdminLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('django_admin:admin_login')
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@gmail.com',
            password='admin123',
            username='adminuser',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='user@gmail.com',
            username='regular',
            password='user123',
            is_staff=False
        )

    def test_admin_login_view_get(self):
        """Test GET request to admin login page"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_admin/login.html')

    def test_successful_admin_login(self):
        """Test successful admin login"""
        response = self.client.post(self.login_url, {
            'email': 'admin@gmail.com',
            'password': 'admin123'
        }, follow=True)
        
        # Check redirect to admin dashboard
        self.assertRedirects(response, reverse('django_admin:admin_dashboard'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Login successful!")

    def test_regular_user_login_attempt(self):
        """Test regular user cannot access admin panel"""
        response = self.client.post(self.login_url, {
            'email': 'user@gmail.com',
            'password': 'user123'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid email or password or insufficient permissions")
        self.assertTemplateUsed(response, 'django_admin/login.html')

    def test_invalid_credentials(self):
        """Test invalid login credentials"""
        response = self.client.post(self.login_url, {
            'email': 'admin@gmail.com',
            'password': 'wrongpassword'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid email or password or insufficient permissions")
        self.assertTemplateUsed(response, 'django_admin/login.html')

    def test_missing_credentials(self):
        """Test missing credentials"""
        response = self.client.post(self.login_url, {
            'email': '',
            'password': ''
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid email or password or insufficient permissions")