
from urllib import request
from django.conf import settings
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.timezone import now
from authUser.models import VetProfile
from coreFunctions.models import Post, ReplyComment, Comment, Category
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()



class AdminCategoryManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            profile_completed=True
        )
        
        # Create test categories
        self.category1 = Category.objects.create(
            name='Pets',
            description='All about pets'
        )
        self.category2 = Category.objects.create(
            name='Veterinary',
            description='Veterinary discussions'
        )
        
        # Create a test post associated with category1
        self.post = Post.objects.create(
            title='Test Post',
            body='Test content',
            category=self.category1,
            user=self.admin_user
        )

    def test_category_management_view(self):
        """Test the category management page loads correctly"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('django_admin:category_management'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_admin/category_management.html')
        
        # Check categories are in context
        categories = response.context['categories']
        self.assertEqual(categories.count(), 2)
        
        # Check post counts are annotated
        pets_category = categories.get(name='Pets')
        self.assertEqual(pets_category.post_count, 1)
        
        # Check admin user is in context
        self.assertEqual(response.context['admin_user'], self.admin_user)

    def test_add_category_success(self):
        """Test successfully adding a new category"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:add_category'),
            {
                'name': 'New Category',
                'description': 'New category description'
            },
            follow=True
        )
        
        # Check category was created
        self.assertTrue(Category.objects.filter(name='New Category').exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('added successfully', str(messages[0]))
        
        # Check redirect
        self.assertRedirects(response, reverse('django_admin:category_management'))

    def test_add_category_duplicate(self):
        """Test adding a duplicate category"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:add_category'),
            {
                'name': 'Pets',  # Already exists
                'description': 'Duplicate category'
            },
            follow=True
        )
        
        # Check category wasn't created again
        self.assertEqual(Category.objects.filter(name='Pets').count(), 1)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('already exists', str(messages[0]))

    def test_edit_category_success(self):
        """Test successfully editing a category"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:edit_category', args=[self.category1.id]),
            {
                'name': 'Updated Pets',
                'description': 'Updated description'
            },
            follow=True
        )
        
        # Check category was updated
        updated_category = Category.objects.get(id=self.category1.id)
        self.assertEqual(updated_category.name, 'Updated Pets')
        self.assertEqual(updated_category.description, 'Updated description')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('updated successfully', str(messages[0]))

    def test_edit_category_duplicate(self):
        """Test editing a category to duplicate another category's name"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:edit_category', args=[self.category1.id]),
            {
                'name': 'Veterinary',  # Already exists for category2
                'description': 'Trying to duplicate'
            },
            follow=True
        )
        
        # Check category wasn't updated
        category = Category.objects.get(id=self.category1.id)
        self.assertEqual(category.name, 'Pets')  # Original name
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('already exists', str(messages[0]))

    def test_delete_category_success(self):
        """Test successfully deleting a category"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:delete_category', args=[self.category1.id]),
            follow=True
        )
        
        # Check category was deleted
        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(id=self.category1.id)
        
        # Check associated post's category was set to None
        post = Post.objects.get(id=self.post.id)
        self.assertIsNone(post.category)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        
        # Check redirect
        self.assertRedirects(response, reverse('django_admin:category_management'))

    def test_category_management_unauthorized(self):
        """Test non-admin users can't access category management"""
        regular_user = User.objects.create_user(
            email='user@example.com',
            username='regular',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        
        self.client.force_login(regular_user)
        
        # Test all category management views
        views = [
            reverse('django_admin:category_management'),
            reverse('django_admin:add_category'),
            reverse('django_admin:edit_category', args=[1]),
            reverse('django_admin:delete_category', args=[1]),
        ]
        
        for view in views:
            response = self.client.get(view, follow=True)
            self.assertRedirects(
                response,
                reverse('django_admin:admin_login'),
                status_code=302,
                target_status_code=200
            )


class AdminDeleteContentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            profile_completed=True
        )
        
        # Create regular user who will own the content
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='regular',            password='testpass123',
            user_type='pet_owner',
            full_name='Regular User'
        )
        
        # Create test post
        self.post = Post.objects.create(
            user=self.regular_user,
            title='Test Post',
            body='This is a test post'
        )
        
        # Create test comment
        self.comment = Comment.objects.create(
            user=self.regular_user,
            post=self.post,
            comment='Test comment'
        )
        
        # Create test reply
        self.reply = ReplyComment.objects.create(
            user=self.regular_user,
            comment=self.comment,
            reply='Test reply'
        )

    # Post deletion tests
    def test_delete_post_success(self):
        """Test successful post deletion"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:delete_post', args=[self.post.id]),
            {'notify_user': 'false'}
        )
        
        # Check post was deleted
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=self.post.id)
            
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        
        # Check redirect
        self.assertRedirects(response, reverse('django_admin:post_management'))

    # Comment deletion tests
    def test_delete_comment_success(self):
        """Test successful comment deletion"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:delete_comment', args=[self.comment.id])
        )
        
        # Check comment was deleted
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=self.comment.id)
            
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        
        # Check redirect
        self.assertRedirects(response, reverse('django_admin:view_post', args=[self.post.id]))

    # Reply deletion tests
    def test_delete_reply_success(self):
        """Test successful reply deletion"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:delete_reply', args=[self.reply.id])
        )
        
        # Check reply was deleted
        with self.assertRaises(ReplyComment.DoesNotExist):
            ReplyComment.objects.get(id=self.reply.id)
            
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        
        # Check redirect
        self.assertRedirects(response, reverse('django_admin:view_post', args=[self.post.id]))

    # Authorization tests
    def test_delete_content_unauthorized(self):
        """Test non-admin cannot delete content"""
        regular_user2 = User.objects.create_user(
            email='user2@example.com',
            username='regular2',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        
        self.client.force_login(regular_user2)
        
        # Try to delete post
        response = self.client.post(
            reverse('django_admin:delete_post', args=[self.post.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Try to delete comment
        response = self.client.post(
            reverse('django_admin:delete_comment', args=[self.comment.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Try to delete reply
        response = self.client.post(
            reverse('django_admin:delete_reply', args=[self.reply.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )

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


class DeclineVetTestCase(TestCase):
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

    def test_decline_vet_success(self):
        """Test successful vet decline by admin"""
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('django_admin:decline_vet', args=[self.vet_profile.id])
        )
        
        self.vet_user.refresh_from_db()
        self.vet_profile.refresh_from_db()
        
        # Check vet was declined
        self.assertFalse(self.vet_user.profile_completed)
        self.assertIsNotNone(self.vet_profile.status_change)
        self.assertRedirects(response, reverse('django_admin:vet_approvals'))

    def test_decline_vet_unauthorized_redirect(self):
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
            reverse('django_admin:decline_vet', args=[self.vet_profile.id]),
            follow=True  # Follow the redirect
        )
        
        # Should redirect to admin login
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Check vet was not declined
        self.vet_user.refresh_from_db()
        self.assertTrue(self.vet_user.profile_completed)

    def test_decline_vet_unauthenticated_redirect(self):
        """Test unauthenticated users are redirected to login"""
        response = self.client.post(
            reverse('django_admin:decline_vet', args=[self.vet_profile.id]),
            follow=True
        )
        
        self.assertRedirects(
            response,
            reverse('django_admin:admin_login'),
            status_code=302,
            target_status_code=200
        )
        
        # Check vet was not declined
        self.vet_user.refresh_from_db()
        self.assertTrue(self.vet_user.profile_completed)

    def test_decline_vet_email_notification(self):
        """Test email notification is sent on successful decline"""
        with patch('django_admin.views.send_mail') as mock_send_mail:
            # Configure the mock to return successfully
            mock_send_mail.return_value = 1  # Indicates 1 email sent
        
            self.client.force_login(self.admin_user)
            response = self.client.post(
                reverse('django_admin:decline_vet', args=[self.vet_profile.id])
            )   
        
        # Check email was sent with correct parameters
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args

        self.assertIn('declined', args[1])
        
        # Verify the vet was still declined
        self.vet_user.refresh_from_db()
        self.assertFalse(self.vet_user.profile_completed)
        
        # Verify redirect
        self.assertRedirects(response, reverse('django_admin:vet_approvals'))


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