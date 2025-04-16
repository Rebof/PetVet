from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
import shortuuid
from .models import Post, Category, Comment, ReplyComment, ChatMessage
from django.utils.text import slugify
from django.utils.timesince import timesince
from django.db.models import Q
from authUser.models import User, PetOwnerProfile
from django.db import models 
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from datetime import datetime






# Create your views here.

# @login_required(login_url='authUser:register')
# def index(request, category_slug=None):
#     posts = Post.objects.all().order_by('-date')
#     categories = Category.objects.annotate(post_count=Count('post'))
#     trending_posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:5]

#     selected_category = None

#     if category_slug:
#         selected_category = get_object_or_404(Category, slug=category_slug)
#         posts = posts.filter(category=selected_category)

#     context = {
#         'posts': posts,
#         'categories': categories,
#         'trending_posts': trending_posts,
#         'selected_category': selected_category,
#     }

#     return render(request, 'coreFunctions/index.html', context)

@login_required(login_url='authUser:register')
def index(request, category_slug=None):
    # Get sort parameter (default to 'newest')
    sort_by = request.GET.get('sort', 'newest')
    
    # Get date filter parameter
    date_filter = request.GET.get('date')
    
    # Start with all posts
    posts_query = Post.objects.all()
    
    # Apply category filter if provided
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        posts_query = posts_query.filter(category=selected_category)
    
    # Apply date filter if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            posts_query = posts_query.filter(date__date=filter_date)
        except ValueError:
            # Invalid date format, ignore filter
            pass
    
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
    
    # Get trending posts (most liked posts)
    trending_posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:5]
    
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
        'date_filter': date_filter,
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

# Add a feed URL that points to the index view
def feed(request):
    """Alias for index view to match the URL in JavaScript"""
    return index(request)

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
            return redirect('coreFunctions:feed')
        
        # Get category
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return redirect('coreFunctions:feed')
        
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
    return redirect('coreFunctions:feed')

# Add a feed URL that points to the index view
def feed(request):
    """Alias for index view to match the URL in JavaScript"""
    return index(request)


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
            return redirect('coreFunctions:feed')
        
        # Get category
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category')
            return redirect('coreFunctions:feed')
        
        # Create slug from title
        slug = slugify(title)
        
        # Check if slug already exists, if so, add a unique identifier
        if Post.objects.filter(slug=slug).exists():
            slug = f"{slug}-{shortuuid.ShortUUID().random(length=6)}"
        
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
    return redirect('coreFunctions:feed')


from django.shortcuts import render, get_object_or_404
from .models import Post, Comment, ReplyComment

def post_detail(request, slug):
    # Get active post by slug
    post = get_object_or_404(Post, slug=slug, active=True)

    # Categories with annotated post counts
    categories = Category.objects.annotate(post_count=Count('post'))

    # Trending posts from same category, excluding current post
    trending_posts = Post.objects.filter(
        category=post.category, active=True
    ).exclude(id=post.id).order_by('-likes')[:5]

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

    if request.method == "POST":
        title = request.POST.get("title")
        category = request.POST.get("category")#outputs 1 as the html has category id in its value
        body = request.POST.get("body")
        image = request.FILES.get("image")

        uid_key = shortuuid.uuid()
        uniqueid = uid_key[:4]
        
        category = get_object_or_404(Category, id=category)  # retrieve the category instance

        if title:
            post = Post(  #can use create here too 
                title=title,
                image=image,
                category=category,
                body=body,
                user=request.user,
                slug=slugify(title) + "-" + str(uniqueid.lower())
            )
            post.save()
            return redirect("coreFunctions:feed")

    return JsonResponse({"data": "sent"})



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
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id, user=request.user)
            post.delete()
            return JsonResponse({'success': True})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Post not found or unauthorized'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

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
def like_post(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            user = request.user

            # Toggle like logic
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True

            return JsonResponse({'success': True, 'likes': post.likes.count(), 'liked': liked})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Post not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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