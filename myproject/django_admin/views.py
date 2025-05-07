from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.timezone import now, timedelta
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
import json
from django.core.serializers.json import DjangoJSONEncoder
from authUser.models import User, VetProfile, PetOwnerProfile
from coreFunctions.models import Post, Category, Comment, ReplyComment
from .decorators import admin_required 

def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('django_admin:admin_dashboard') 
        else:
            messages.error(request, "Invalid email or password or insufficient permissions")
    return render(request, 'django_admin/login.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect('django_admin:admin_login')

@admin_required
def admin_dashboard(request):
    # Get counts for dashboard stats
    total_users = User.objects.count()
    total_vets = User.objects.filter(user_type='vet').count()
    total_pet_owners = User.objects.filter(user_type='pet_owner').count()
    total_posts = Post.objects.count()
    
    # Get pending vet approvals
    pending_vets = VetProfile.objects.filter(
        user__status_verification=False,
        user__profile_completed=True,
        user__user_type='vet'
    )[:5]  # Limit to 5 for dashboard
    
    # Get recent posts
    recent_posts = Post.objects.all().order_by('-date')[:5]
    
    # Get post counts by category for chart - modified to ensure proper JSON serialization
    categories = Category.objects.annotate(post_count=Count('post')).order_by('-post_count')
    category_data = [
        {'name': category.name, 'count': category.post_count}
        for category in categories
    ]
    
    return render(request, 'django_admin/dashboard.html', {
        'total_users': total_users,
        'total_vets': total_vets,
        'total_pet_owners': total_pet_owners,
        'total_posts': total_posts,
        'pending_vets': pending_vets,
        'recent_posts': recent_posts,
        'category_data': json.dumps(category_data, cls=DjangoJSONEncoder),  # Single JSON object
        'admin_user': request.user,
        'active_page': 'dashboard'
    })

@admin_required
def user_management(request):
    search_query = request.GET.get('search', '')
    user_type = request.GET.get('user_type', '')
    
    # Filter users based on search and user type
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) | 
            Q(full_name__icontains=search_query)
        )
    
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Paginate results
    paginator = Paginator(users.order_by('-date_joined'), 10)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    return render(request, 'django_admin/user_management.html', {
        'users': users,
        'admin_user': request.user,
        'active_page': 'users'
    })

@admin_required
def view_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get user profile based on user type
    profile = None
    if user.user_type == 'vet':
        profile = VetProfile.objects.filter(user=user).first()
    elif user.user_type == 'pet_owner':
        profile = PetOwnerProfile.objects.filter(user=user).first()
    
    # Get user posts
    posts = Post.objects.filter(user=user).order_by('-date')
    
    return render(request, 'django_admin/view_user.html', {
        'user_obj': user,
        'profile': profile,
        'posts': posts,
        'admin_user': request.user,
        'active_page': 'users'
    })

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Send email notification
        try:
            send_mail(
                'Your PetVet Account Has Been Deleted',
                f'Dear {user.full_name or user.username},\n\nYour account on PetVet has been deleted by an administrator. If you believe this is an error, please contact our support team.\n\nBest regards,\nThe PetVet Team',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(request, f"User deleted but email notification failed: {str(e)}")
        
        # Delete the user
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' has been deleted successfully.")
        
        return redirect('django_admin:user_management')
    
    return redirect('django_admin:view_user', user_id=user_id)

@admin_required
def post_management(request):
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    # Filter posts based on search and category
    posts = Post.objects.all()
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(body__icontains=search_query)
        )
    
    if category_id:
        posts = posts.filter(category_id=category_id)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    # Paginate results
    paginator = Paginator(posts.order_by('-date'), 10)
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
    return render(request, 'django_admin/post_management.html', {
        'posts': posts,
        'categories': categories,
        'admin_user': request.user,
        'active_page': 'posts'
    })

@admin_required
def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('-date')
    
    return render(request, 'django_admin/view_post.html', {
        'post': post,
        'comments': comments,
        'admin_user': request.user,
        'active_page': 'posts'
    })

@admin_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        # Check if we should notify the user
        notify_user = request.POST.get('notify_user') == 'true'
        
        if notify_user:
            try:
                send_mail(
                    'Your Post Has Been Removed',
                    f'Dear {post.user.full_name or post.user.username},\n\nYour post "{post.title}" has been removed by an administrator for violating our community guidelines. If you believe this is an error, please contact our support team.\n\nBest regards,\nThe PetVet Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [post.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(request, f"Post deleted but email notification failed: {str(e)}")
        
        # Delete the post
        post_title = post.title
        post.delete()
        messages.success(request, f"Post '{post_title}' has been deleted successfully.")
        
        return redirect('django_admin:post_management')
    
    return redirect('django_admin:view_post', post_id=post_id)



@admin_required
def toggle_post_status(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        # Toggle the active status
        post.active = not post.active
        post.save()
        
        status = "activated" if post.active else "deactivated"
        messages.success(request, f"Post '{post.title}' has been {status} successfully.")
        
        # Notify the user
        try:
            if not post.active:  # Only notify when deactivating
                send_mail(
                    'Your Post Has Been Deactivated',
                    f'Dear {post.user.full_name or post.user.username},\n\nYour post "{post.title}" has been deactivated by an administrator. If you believe this is an error, please contact our support team.\n\nBest regards,\nThe PetVet Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [post.user.email],
                    fail_silently=False,
                )
        except Exception as e:
            messages.warning(request, f"Post status changed but email notification failed: {str(e)}")
    
    return redirect('django_admin:view_post', post_id=post_id)

@admin_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comment has been deleted successfully.")
    
    return redirect('django_admin:view_post', post_id=post_id)

@admin_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(ReplyComment, id=reply_id)
    post_id = reply.comment.post.id
    
    if request.method == 'POST':
        reply.delete()
        messages.success(request, "Reply has been deleted successfully.")
    
    return redirect('django_admin:view_post', post_id=post_id)

@admin_required
def vet_approvals(request):
    # Get pending vet approvals
    pending_vets = VetProfile.objects.filter(
        user__status_verification=False,
        user__profile_completed=True,
        user__user_type='vet'
    )
    
    # Get recently approved vets (approved in the last 7 days)
    recently_approved_vets = VetProfile.objects.filter(
        user__status_verification=True,
        status_change__gte=now() - timedelta(days=7)
    )
    
    # Get recently declined vets (declined in the last 7 days)
    recently_declined_vets = VetProfile.objects.filter(
        user__status_verification=False,
        user__profile_completed=False,
        status_change__gte=now() - timedelta(days=7)
    )
    
    return render(request, 'django_admin/vet_approvals.html', {
        'pending_vets': pending_vets,
        'recently_approved_vets': recently_approved_vets,
        'recently_declined_vets': recently_declined_vets,
        'admin_user': request.user,
        'active_page': 'vet_approvals'
    })

@admin_required
def view_vet(request, vet_id):
    vet_profile = get_object_or_404(VetProfile, id=vet_id)
    
    return render(request, 'django_admin/view_vet.html', {
        'vet': vet_profile,
        'admin_user': request.user,
        'active_page': 'vet_approvals'
    })

#tested
@admin_required
def approve_vet(request, vet_id):
    vet_profile = get_object_or_404(VetProfile, id=vet_id)
    vet_user = vet_profile.user
    
    vet_user.status_verification = True
    vet_profile.verified = True
    vet_profile.status_change = now()
    
    vet_user.save()
    vet_profile.save()
    
    # Send email notification
    try:
        send_mail(
            'Your Veterinarian Account Has Been Approved',
            f'Dear {vet_user.full_name or vet_user.username},\n\nCongratulations! Your veterinarian account on PetVet has been approved. You can now access all veterinarian features on the platform.\n\nBest regards,\nThe PetVet Team',
            settings.DEFAULT_FROM_EMAIL,
            [vet_user.email],
            fail_silently=False,
        )
    except Exception as e:
        messages.warning(request, f"Vet approved but email notification failed: {str(e)}")
    
    messages.success(request, f"Veterinarian '{vet_user.full_name or vet_user.username}' has been approved successfully.")
    return redirect('django_admin:vet_approvals')


@admin_required
def decline_vet(request, vet_id):
    vet_profile = get_object_or_404(VetProfile, id=vet_id)
    vet_user = vet_profile.user
    
    vet_user.profile_completed = False
    vet_profile.status_change = now()
    
    vet_user.save()
    vet_profile.save()
    
    # Prepare email details
    subject = 'Your Veterinarian Account Application'
    message = f'Dear {vet_user.full_name or vet_user.username},\n\nWe regret to inform you that your application to register as a veterinarian on PetVet has been declined. This may be due to incomplete or incorrect information provided. Please update your profile with accurate information and try again.\n\nBest regards,\nThe PetVet Team'
    recipient = [vet_user.email]
    
    # Send email notification
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient,
            fail_silently=False,
        )
    except Exception as e:
        messages.warning(request, f"Vet declined but email notification failed: {str(e)}")
    
    messages.success(request, f"Veterinarian '{vet_user.full_name or vet_user.username}' has been declined.")
    return redirect('django_admin:vet_approvals')


@admin_required
def category_management(request):
    # Get all categories with post count
    categories = Category.objects.annotate(post_count=Count('post'))
    
    return render(request, 'django_admin/category_management.html', {
        'categories': categories,
        'admin_user': request.user,
        'active_page': 'categories'
    })


@admin_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if Category.objects.filter(name=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
        else:
            category = Category.objects.create(name=name, description=description)
            messages.success(request, f"Category '{name}' has been added successfully.")
    
    return redirect('django_admin:category_management')


@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        # Check if name already exists for another category
        if Category.objects.filter(name=name).exclude(id=category_id).exists():
            messages.error(request, f"Category '{name}' already exists.")
        else:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, f"Category '{name}' has been updated successfully.")
    
    return redirect('django_admin:category_management')


@admin_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = category.name
        
        # Update posts to remove category reference
        Post.objects.filter(category=category).update(category=None)
        
        category.delete()
        messages.success(request, f"Category '{name}' has been deleted successfully.")
    
    return redirect('django_admin:category_management')
