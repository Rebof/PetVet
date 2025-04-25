from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from coreFunctions.models import Post, Category, ReplyComment, Comment, ChatMessage
from channels.testing import WebsocketCommunicator
from asgiref.sync import async_to_sync
from coreFunctions.consumers import ChatConsumer, NotificationConsumer
import datetime
from coreFunctions.routing import websocket_urlpatterns
from asgiref.sync import sync_to_async



User = get_user_model()

class ChatConsumerTestCase(TestCase):
    def setUp(self):
        """Initialize test users and their profiles"""
        # Create pet owner user and profile
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.pet_owner_profile = self.user1.petownerprofile  # Access profile via reverse relation
        
        # Create vet user and profile
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            user_type='vet',
            profile_completed=True,
            status_verification=True
        )
        self.vet_profile = self.user2.vetprofile  # Access profile via reverse relation
        
        # Create unique room name for chat
        self.room_name = f"chat_{self.user1.id}_{self.user2.id}"

    async def test_chat_connection(self):
        """Test basic WebSocket connection setup"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        # Manually add URL route params to scope
        communicator.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_chat_message_exchange(self):
        """Test complete message flow between two connected users"""
        # Setup first user connection
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator1.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator1.connect()
        
        # Setup second user connection
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator2.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator2.connect()
        # Send test message from user1
        test_message = "Hello from User1!"
        await communicator1.send_json_to({
            'message': test_message,
            'sender': 'user1',
            'receiver': 'user2',
            'timestamp': datetime.datetime.now().isoformat()
        })

        # Verify user2 receives the message
        response = await communicator2.receive_json_from()
        self.assertEqual(response['message'], test_message)
        self.assertEqual(response['sender'], 'user1')
        self.assertEqual(response['receiver'], 'user2')
        
        # Clean up connections
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_message_persistence(self):
        """Verify messages are properly saved to database"""
        # Get initial message count
        initial_count = await sync_to_async(ChatMessage.objects.count)()
        
        # Setup connection and send test message
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator.connect()
        
        test_msg_content = "This is a Test persistence message"
        await communicator.send_json_to({
            'message': test_msg_content,
            'sender': 'user1',
            'receiver': 'user2',
            'timestamp': datetime.datetime.now().isoformat()
        })
        await communicator.disconnect()
        
        # Verify message was saved
        final_count = await sync_to_async(ChatMessage.objects.count)()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify message content and participants
        message = await sync_to_async(ChatMessage.objects.last)()
        self.assertEqual(message.message.lower(), test_msg_content.lower())  # Case-insensitive check
        self.assertEqual(await sync_to_async(lambda: message.sender.username)(), 'user1')
        self.assertEqual(await sync_to_async(lambda: message.receiver.username)(), 'user2')

    async def test_notification_flow(self):
        """Test notification system triggers properly"""
        # Connect user2 to notifications
        notif_communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            f"/ws/notifications/{self.user2.username}/"
        )
        notif_communicator.scope.update({
            'url_route': {
                'kwargs': {'username': self.user2.username}
            }
        })
        await notif_communicator.connect()
        
        # Connect user1 to chat and send message
        chat_communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        chat_communicator.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await chat_communicator.connect()
        
        test_message = "This should trigger notification"
        await chat_communicator.send_json_to({
            'message': test_message,
            'sender': 'user1',
            'receiver': 'user2',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Verify user2 receives notification
        notif_response = await notif_communicator.receive_json_from()
        self.assertEqual(notif_response['type'], 'new_message')
        self.assertEqual(notif_response['message'], test_message)
        self.assertEqual(notif_response['sender'], 'user1')
        
        # Clean up
        await notif_communicator.disconnect()
        await chat_communicator.disconnect()

    async def test_invalid_user_handling(self):
        """Test system handles invalid users gracefully"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator.connect()
        
        # Test invalid user doesn't crash system
        await communicator.send_json_to({
            'message': 'Test message',
            'sender': 'user1',
            'receiver': 'nonexistent_user',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Verify valid message still works
        valid_msg = 'Hello! Valid message'
        await communicator.send_json_to({
            'message': valid_msg,
            'sender': 'user1',
            'receiver': 'user2',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['message'], valid_msg)
        
        await communicator.disconnect()

    async def test_concurrent_messaging(self):
        """Test handling of multiple rapid messages"""
        # Setup sender and receiver connections
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator1.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator1.connect()
        
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.room_name}/"
        )
        communicator2.scope.update({
            'url_route': {
                'kwargs': {'room_name': self.room_name}
            }
        })
        await communicator2.connect()
        
        # Send multiple messages quickly
        messages = ["Message 1", "Message 2", "Message 3"]
        for msg in messages:
            await communicator1.send_json_to({
                'message': msg,
                'sender': 'user1',
                'receiver': 'user2',
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        # Verify all messages arrive in order
        for expected_msg in messages:
            response = await communicator2.receive_json_from()
            self.assertEqual(response['message'], expected_msg)
        
        # Clean up
        await communicator1.disconnect()
        await communicator2.disconnect()

class PostEditLikeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.pet_owner_profile = self.user.petownerprofile
        self.client.force_login(self.user)

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create a test post
        self.post = Post.objects.create(
            title='Test Post',
            body='Test Content',
            user=self.user,
            category=self.category,
            slug='test-post'
        )

    # Edit Post Tests
    def test_edit_post_success(self):
        """Test successful post editing"""
        response = self.client.post(
            reverse('coreFunctions:edit_post', kwargs={'slug': self.post.slug}),
            {
                'title': 'Updated Title',
                'body': 'Updated Content',
                'category': self.category.id
            }
        )
        
        # Verify redirect to post detail
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('coreFunctions:post-detail', kwargs={'slug': self.post.slug}))
        
        # Refresh post from db
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.body, 'Updated Content')

    def test_edit_post_with_image(self):
        """Test post editing with image upload"""
        image = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        
        response = self.client.post(
            reverse('coreFunctions:edit_post', kwargs={'slug': self.post.slug}),
            {
                'title': 'Post with Image',
                'body': 'Content',
                'category': self.category.id,
                'image': image
            },
            format='multipart/form-data'
        )
        
        # Refresh post from db
        self.post.refresh_from_db()
        self.assertTrue(bool(self.post.image))
        self.assertEqual(response.status_code, 302)

    def test_edit_post_unauthorized(self):
        """Test unauthorized user cannot edit post"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        
        # Create post owned by other user
        other_post = Post.objects.create(
            title='Other Post',
            body='Content',
            user=other_user,
            category=self.category,
            slug='other-post'
        )
        
        response = self.client.post(
            reverse('coreFunctions:edit_post', kwargs={'slug': other_post.slug}),
            {
                'title': 'Try to Edit',
                'body': 'Should not work',
                'category': self.category.id
            }
        )
        
        # Should return 404 since post doesn't belong to user
        self.assertEqual(response.status_code, 404)

    # Like Post Tests
    def test_like_post_success(self):
        """Test successful like/unlike toggle"""
        # First like
        response = self.client.post(
            reverse('coreFunctions:like_post', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Simulate AJAX
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'success',
            'likes_count': 1,
            'liked': True
        })
        
        # Then unlike
        response = self.client.post(
            reverse('coreFunctions:like_post', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'success',
            'likes_count': 0,
            'liked': False
        })

    def test_like_post_invalid_method(self):
        """Test like post with invalid HTTP method"""
        response = self.client.get(
            reverse('coreFunctions:like_post', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'status': 'error',
            'message': 'Invalid request'
        })

class CommentViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.client.force_login(self.user)

        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.post = Post.objects.create(
            title='Test Post',
            body='Test Content',
            user=self.user,
            category=self.category,
            slug='test-post'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            comment='Test comment'
        )

    # Like Comment Tests
    def test_like_comment_success(self):
        """Test successful like/unlike toggle"""
        # First like
        response = self.client.post(
            reverse('coreFunctions:like_comment', args=[self.comment.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'success': True,
            'likes': 1,
            'liked': True
        })

        # Then unlike
        response = self.client.post(
            reverse('coreFunctions:like_comment', args=[self.comment.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'success': True,
            'likes': 0,
            'liked': False
        })

    def test_like_comment_invalid_comment(self):
        """Test like non-existent comment shows 404 page"""
        response = self.client.post(
            reverse('coreFunctions:like_comment', args=[999]),  # Invalid comment ID
            follow=True  # Follow redirect to 404 page
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    # Delete Comment Tests
    def test_delete_comment_success(self):
        """Test successful comment deletion"""
        response = self.client.post(
            reverse('coreFunctions:delete_comment', args=[self.comment.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_unauthorized(self):
        """Test unauthorized comment deletion shows 404 page"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            profile_completed=True,
            status_verification=True
        )
        other_comment = Comment.objects.create(
            post=self.post,
            user=other_user,
            comment='Other comment'
        )
        response = self.client.post(
            reverse('coreFunctions:delete_comment', args=[other_comment.id]),
            follow=True  # Follow redirect to 404 page
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    # Add Comment Tests
    def test_add_comment_success(self):
        """Test successful comment creation"""
        response = self.client.post(
            reverse('coreFunctions:add_comment', kwargs={'slug': self.post.slug}),
            {'comment': 'New test comment'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('comment_html', response_data)
        self.assertIn('comment_id', response_data)
        self.assertTrue(Comment.objects.filter(id=response_data['comment_id']).exists())

    def test_add_comment_empty(self):
        """Test comment with empty content"""
        response = self.client.post(
            reverse('coreFunctions:add_comment', kwargs={'slug': self.post.slug}),
            {'comment': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'success': False,
            'error': 'Comment cannot be empty'
        })

    def test_add_comment_invalid_post(self):
        """Test comment on non-existent post shows 404 page"""
        response = self.client.post(
            reverse('coreFunctions:add_comment', kwargs={'slug': 'non-existent-slug'}),
            {'comment': 'Test comment'},
            follow=True  # Follow redirect to 404 page
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

class ReplyViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
        self.client.force_login(self.user)

        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.post = Post.objects.create(
            title='Test Post',
            body='Test Content',
            user=self.user,
            category=self.category,
            slug='test-post'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            comment='Test comment'
        )

    # Delete Reply Tests
    def test_delete_reply_success(self):
        """Test successful reply deletion"""
        reply = ReplyComment.objects.create(
            comment=self.comment,
            user=self.user,
            reply='Test reply'
        )
        response = self.client.post(
            reverse('coreFunctions:delete_reply', args=[reply.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        self.assertFalse(ReplyComment.objects.filter(id=reply.id).exists())

    def test_delete_reply_unauthorized(self):
        """Test unauthorized reply deletion returns 404 page"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        reply = ReplyComment.objects.create(
            comment=self.comment,
            user=other_user,  # Owned by different user
            reply='Test reply'
        )
        response = self.client.post(
            reverse('coreFunctions:delete_reply', args=[reply.id]),
            follow=True  # Follow redirect to 404 page
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')  # Verify 404 page is shown

    def test_delete_reply_invalid_method(self):
        """Test reply deletion with invalid HTTP method"""
        reply = ReplyComment.objects.create(
            comment=self.comment,
            user=self.user,
            reply='Test reply'
        )
        response = self.client.get(
            reverse('coreFunctions:delete_reply', args=[reply.id])
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'success': False,
            'error': 'Invalid request method'
        })

    # Add Reply Tests
    def test_add_reply_success(self):
        """Test successful reply creation"""
        response = self.client.post(
            reverse('coreFunctions:add_reply', args=[self.comment.id]),
            {'reply': 'Test reply content'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('reply_html', response_data)
        self.assertIn('reply_id', response_data)
        self.assertTrue(ReplyComment.objects.filter(id=response_data['reply_id']).exists())

    def test_add_reply_empty(self):
        """Test reply with empty content"""
        response = self.client.post(
            reverse('coreFunctions:add_reply', args=[self.comment.id]),
            {'reply': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'success': False,
            'error': 'Reply cannot be empty'
        })

    def test_add_reply_invalid_comment(self):
        """Test reply to non-existent comment shows 404 page"""
        response = self.client.post(
            reverse('coreFunctions:add_reply', args=[999]),  # Invalid comment ID
            {'reply': 'Test reply'},
            follow=True  # Follow redirect to 404 page
        )
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')  # Verify 404 page is shown

    def test_add_reply_invalid_method(self):
        """Test add reply with invalid HTTP method"""
        response = self.client.get(
            reverse('coreFunctions:add_reply', args=[self.comment.id])
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'success': False,
            'error': 'Invalid request'
        })

class PostViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
        self.user = User.objects.create_user(
            username='petowner',
            email='owner@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )
    
        self.pet_owner_profile = self.user.petownerprofile
        self.client.force_login(self.user)

        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_create_post_success(self):
        """Test post creation redirects to post-detail"""
        response = self.client.post(
            reverse('coreFunctions:create-post'),
            {
                'title': 'New Test Post',
                'body': 'Test content',
                'category': self.category.id
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('coreFunctions:post-detail', 
                             kwargs={'slug': Post.objects.last().slug}))

    def test_create_post_with_image(self):
        """Test image upload redirects to post-detail"""
        image = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        response = self.client.post(
            reverse('coreFunctions:create-post'),
            {
                'title': 'Post with Image',
                'body': 'Test content',
                'category': self.category.id,
                'image': image
            },
            format='multipart/form-data'
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/post/'))

    def test_create_post_unauthenticated(self):
        """Test unauthenticated user cannot create post"""
        # Logout the current user
        self.client.logout()
        
        initial_count = Post.objects.count()
        
        response = self.client.post(
            reverse('coreFunctions:create-post'),
            {
                'title': 'Unauthenticated Post',
                'body': 'Should not work',
                'category': self.category.id
            }
        )
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        
        # No new post should be created
        self.assertEqual(Post.objects.count(), initial_count)

    def test_delete_post_success(self):
        """Test post deletion returns JSON success"""
        post = Post.objects.create(
            title='Test Delete Post',
            body='Content',
            user=self.user,
            category=self.category,
            slug='test-delete-post'
        )
        response = self.client.post(
            reverse('coreFunctions:delete_post', args=[post.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_delete_post_invalid_method(self):
        """Test GET request returns JSON error"""
        post = Post.objects.create(
            title='Invalid Method Post',
            body='Content',
            user=self.user, 
            category=self.category,
            slug='invalid-method-post'
        )
        response = self.client.get(
            reverse('coreFunctions:delete_post', args=[post.id])
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'success': False,
            'error': 'Invalid request method'
        })

    def test_delete_post_unauthorized(self):
        """Test unauthorized deletion returns JSON error"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            user_type='pet_owner',
            profile_completed=True,
            status_verification=True
        )

        # Create post owned by main user
        post = Post.objects.create(
            title='Unauthorized Post',
            body='Content',
            user=self.user,
            category=self.category,
            slug='unauthorized-post'
        )

        # Get initial count
        initial_count = Post.objects.count()

        # Switch to other user and attempt deletion
        self.client.force_login(other_user)
        self.client.post(
            reverse('coreFunctions:delete_post', args=[post.id])
        )

        # Verify post still exists and count unchanged
        self.assertEqual(Post.objects.count(), initial_count)
        self.assertTrue(Post.objects.filter(id=post.id).exists())