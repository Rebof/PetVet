from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
import shortuuid
from .models import Post, Category, Comment, ReplyComment, ChatMessage
from django.utils.text import slugify
from django.utils.timesince import timesince
from django.db.models import Q
from authUser.models import User, PetOwnerProfile, VetProfile
from django.db import models 
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from random import sample
from django.db.models import Count, IntegerField, ExpressionWrapper
from django.core.mail import send_mail


@login_required(login_url='authUser:register')
def index(request, category_slug=None):
    # Get sort parameter (default to 'newest')
    sort_by = request.GET.get('sort', 'newest')
    
    # Get date filter parameter
    date_filter = request.GET.get('date')
    
    # Start with all posts
    posts_query = Post.objects.filter(active=True)
    
    # Apply category filter if provided
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        posts_query = posts_query.filter(category=selected_category)

    
     # Apply sorting
    if sort_by == 'likes':
        # Sort by most likes
        posts = posts_query.annotate(like_count=Count('likes')).order_by('-like_count')
    elif sort_by == 'comments':
        # Sort by most comments
        posts = posts_query.annotate(comment_count=Count('comments')).order_by('-comment_count')
    elif sort_by == 'oldest':
        # Sort by oldest first
        posts = posts_query.order_by('date')
    else:
        # Default: sort by newest
        posts = posts_query.order_by('-date')
    
    # Get all categories with post count
    categories = Category.objects.annotate(post_count=Count('post'))
    
    posts_with_engagement = Post.objects.annotate(
    like_count=Count('likes'),
    comment_count=Count('comments'),
    engagement_score=ExpressionWrapper(
        Count('likes') + Count('comments'),
        output_field=IntegerField()
    )
).order_by('-engagement_score')[:10]  # top 10 by total engagement

# Pick 5 random ones from top 10
    trending_posts = sample(list(posts_with_engagement), min(5, len(posts_with_engagement)))

    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only the posts HTML for AJAX requests
        return render(request, 'main/partials/feed_posts.html', {'posts': posts})
    
    context = {
        'posts': posts,
        'categories': categories,
        'trending_posts': trending_posts,
        'selected_category': selected_category,
        'sort_by': sort_by,
    }
    
    return render(request, 'coreFunctions/index.html', context)

@login_required
def like_post(request, post_id):
    """Handle post liking via AJAX"""
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            user = request.user
            
            # Toggle like
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
            
            return JsonResponse({
                'status': 'success',
                'likes_count': post.likes.count(),
                'liked': liked
            })
        except Post.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        # Validate required fields
        if not title or not body or not category_id:
            messages.error(request, 'Please fill in all required fields')
            return redirect('coreFunctions:index')
        
        # Get category
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return redirect('coreFunctions:index')
        # Create slug from title
        slug = slugify(title)
        # Check if slug already exists, if so, add a unique identifier
        if Post.objects.filter(slug=slug).exists():
            slug = f"{slug}-{shortuuid.uuid()[:6]}"
        # Create post
        post = Post.objects.create(
            title=title,
            body=body,
            category=category,
            user=request.user,
            slug=slug
        )
        # Add image if provided
        if image:
            post.image = image
            post.save()
        
        messages.success(request, 'Post created successfully')
        return redirect('coreFunctions:post-detail', slug=post.slug)

    # If not POST, redirect to feed
    return redirect('coreFunctions:index')


def feed(request):
    """Alias for index view to match the URL in JavaScript"""
    return index(request)



def post_detail(request, slug):
    # Get active post by slug
    post = get_object_or_404(Post, slug=slug, active=True)

    # Categories with annotated post counts
    categories = Category.objects.annotate(post_count=Count('post'))


    posts_with_engagement = Post.objects.filter(
    category=post.category,  # assuming `post` is defined
    active=True
).annotate(
    like_count=Count('likes'),
    comment_count=Count('comments'),
    engagement_score=ExpressionWrapper(
        Count('likes') + Count('comments'),
        output_field=IntegerField()
    )
).order_by('-engagement_score')[:10] # top 10 by total engagement

    # Pick 5 random ones from top 10
    trending_posts = sample(list(posts_with_engagement), min(5, len(posts_with_engagement)))    

    # Active comments and their active replies
    comments = post.comments.filter(active=True).prefetch_related(
        models.Prefetch(
            'replies',
            queryset=ReplyComment.objects.filter(active=True),
            to_attr='active_replies'
        )
    )

    context = {
        'post': post,
        'categories': categories,
        'trending_posts': trending_posts,
        'comments': comments,
    }
    return render(request, 'coreFunctions/post_detail.html', context)



def home(request):
    return render(request, 'coreFunctions/landing.html')

def about(request):
    return render(request, 'coreFunctions/about.html')

def community(request):
    return render(request, 'coreFunctions/community.html')

def contact(request):
    return render(request, 'coreFunctions/contact.html')

def appointment(request):
    return render(request, 'coreFunctions/appointment.html')




@login_required
def inbox_details(request, username=None):
    sender = request.user
    receiver = None
    messages_detail = None

    if username:
        receiver = get_object_or_404(User, username=username)
        # Fetch conversation between sender and receiver, ordered by date
        messages_detail = ChatMessage.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).order_by("date")
        # Mark received messages as read
        messages_detail.filter(receiver=sender).update(is_read=True)

    # Get recent conversations for sidebar
    recent_messages = ChatMessage.objects.filter(
        Q(sender=sender) | Q(receiver=sender)
    ).order_by("-date")

    # Organize conversations by partner, keeping the latest message
    conversation_partners = {}
    for message in recent_messages:
        if not message.sender or not message.receiver:
            continue
        partner = message.sender if message.sender != sender else message.receiver
        if partner.id not in conversation_partners:
            conversation_partners[partner.id] = message

    context = {
        "message_detail": messages_detail,
        "receiver": receiver,
        "message_list": conversation_partners.values(),
    }
    return render(request, 'chat/inbox_detail.html', context)

def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug, user=request.user)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        body = request.POST.get('body')
        category_id = request.POST.get('category')
        
        # Validate required fields
        if not title:
            messages.error(request, "Title is required")
            return redirect('edit_post', slug=post.slug)
        
        # Update post fields
        post.title = title
        post.body = body if body else None
        
        # Handle category
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                post.category = category
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected")
                return redirect('edit_post', slug=post.slug)
        
        # Handle image removal/replacement
        if 'remove_image' in request.POST and request.POST['remove_image'] == 'true':
            if post.image:
                post.image.delete(save=False)
            post.image = None
        
        # Handle video removal/replacement
        if 'remove_video' in request.POST and request.POST['remove_video'] == 'true':
            if post.video:
                post.video.delete(save=False)
            post.video = None
        
        # Handle new image upload
        if 'new_image' in request.FILES:
            if post.image:  # Delete old image if exists
                post.image.delete(save=False)
            post.image = request.FILES['new_image']
        
        # Handle new video upload
        if 'new_video' in request.FILES:
            if post.video:  # Delete old video if exists
                post.video.delete(save=False)
            post.video = request.FILES['new_video']
        
        # Handle replacing existing media
        if 'image' in request.FILES:
            if post.image:  # Delete old image if exists
                post.image.delete(save=False)
            post.image = request.FILES['image']
        
        if 'video' in request.FILES:
            if post.video:  # Delete old video if exists
                post.video.delete(save=False)
            post.video = request.FILES['video']
        
        # Save the post
        post.save()
        messages.success(request, "Post updated successfully")
        return redirect('coreFunctions:post-detail', slug=post.slug)
    
    context = {
        'post': post,
        'categories': categories,
    }
    return render(request, 'coreFunctions/edit_post.html', context)


@login_required
def delete_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=400, content_type='application/json')

    try:
        post = Post.objects.get(id=post_id)
        if post.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Post not found or unauthorized'
            }, status=404, content_type='application/json')
        
        post.delete()
        return JsonResponse({'success': True}, content_type='application/json')
        
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post not found'
        }, status=404, content_type='application/json')

@login_required
def delete_comment(request, comment_id):
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
            comment.delete()
            return JsonResponse({'success': True})
        except Comment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Comment not found or unauthorized'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def delete_reply(request, reply_id):
    if request.method == 'POST':
        try:
            reply = ReplyComment.objects.get(id=reply_id, user=request.user)
            reply.delete()
            return JsonResponse({'success': True})
        except ReplyComment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Reply not found or unauthorized'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required
def like_comment(request, comment_id):
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            user = request.user

            if user in comment.likes.all():
                comment.likes.remove(user)
                liked = False
            else:
                comment.likes.add(user)
                liked = True

            return JsonResponse({'success': True, 'likes': comment.likes.count(), 'liked': liked})
        except Comment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def add_reply(request, comment_id):
    if request.method == 'POST':
        try:
            parent_comment = Comment.objects.get(id=comment_id)
            reply_text = request.POST.get('reply', '').strip()
            
            if not reply_text:
                return JsonResponse({'success': False, 'error': 'Reply cannot be empty'}, status=400)
            
            # Create the reply
            reply = ReplyComment.objects.create(
                comment=parent_comment,
                user=request.user,
                reply=reply_text
            )
            
            # Return the new reply as HTML
            reply_html = render_to_string('main/partials/reply.html', {
                'reply': reply,
                'request': request
            })
            
            return JsonResponse({
                'success': True,
                'reply_html': reply_html,
                'reply_id': reply.id
            })
            
        except Comment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def search_results(request):
    query = request.GET.get('q', '')
    
    if query:
        # Search for posts by title or body
        posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(body__icontains=query)
        )
        
        # Search for vet profiles
        vets = VetProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__full_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)  
        )
        
        # Search for pet owner profiles
        pet_owners = PetOwnerProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__full_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    else:
        posts = Post.objects.none()
        vets = VetProfile.objects.none()
        pet_owners = PetOwnerProfile.objects.none()
    
    context = {
        'query': query,
        'posts': posts,
        'vets': vets,
        'pet_owners': pet_owners,
    }
    
    return render(request, 'main/search_results.html', context)


def contact(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        

        
        # Basic validation
        if not all([name, email, subject, message]):
            messages.error(request, "All fields are required!")
            return redirect('coreFunctions:contact')
        
        if '@' not in email:
            messages.error(request, "Please enter a valid email address")
            return redirect('corefunctions:contact')
        
        try:
            # Format the email content
            email_subject = f"Contact Form: {subject}"
            email_message = (
    f"Hello Admin,\n\n"
    f"You have received a new message through the contact form.\n\n"
    f"Name: {name}\n"
    f"Email: {email}\n\n"
    f"Message:\n{message}\n\n"
    f"Best regards,\n"
    f"The PetVet Website"
)
            
            # Send email (consistent with your working OTP code)
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,  # From email
                [settings.CONTACT_EMAIL],     # To email
                fail_silently=False,
            )
            
            messages.success(request, "Your message has been sent successfully!")
            return redirect('coreFunctions:contact')
            
        except Exception as e:
            messages.error(request, f"Failed to send message. Error: {str(e)}")
            return redirect('coreFunctions:contact')
    
    return render(request, 'coreFunctions/contact.html')


def add_comment(request, slug):
    if request.method == 'POST':
        try:
            post = Post.objects.get(slug=slug)
            comment_text = request.POST.get('comment', '').strip()
            
            if not comment_text:
                return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
            
            # Create the comment
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                comment=comment_text
            )
            
            # Return the new comment as HTML
            comment_html = render_to_string('main/partials/comment.html', {
                'comment': comment,
                'request': request
            })
            
            return JsonResponse({
                'success': True,
                'comment_html': comment_html,
                'comment_id': comment.id
            })
            
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)