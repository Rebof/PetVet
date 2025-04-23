from django.urls import path
from . import views

app_name = 'django_admin'

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.view_user, name='view_user'),
    # path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Post management
    path('posts/', views.post_management, name='post_management'),
    path('posts/<int:post_id>/', views.view_post, name='view_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/toggle-status/', views.toggle_post_status, name='toggle_post_status'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('replies/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),
    
    # Vet approvals
    path('vet-approvals/', views.vet_approvals, name='vet_approvals'),
    path('vet-approvals/<int:vet_id>/', views.view_vet, name='view_vet'),
    path('vet-approvals/<int:vet_id>/approve/', views.approve_vet, name='approve_vet'),
    path('vet-approvals/<int:vet_id>/decline/', views.decline_vet, name='decline_vet'),
    
    # Category management
    path('categories/', views.category_management, name='category_management'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
]
