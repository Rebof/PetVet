
from django.urls import path

from . import views
app_name = "coreFunctions"

urlpatterns = [
    path("", views.index, name="index"),
    path('category/<slug:category_slug>/', views.index, name='category_posts'),

    path("create-post/", views.create_post, name="create-post"),


    path('post/<str:slug>/', views.post_detail, name='post-detail'),
    path('edit-post/<slug:slug>/', views.edit_post, name='edit_post'),

    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete-reply/<int:reply_id>/', views.delete_reply, name='delete_reply'),

    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('add-reply/<int:comment_id>/', views.add_reply, name='add_reply'),

    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('like-comment/<int:comment_id>/', views.like_comment, name='like_comment'),


    path('inbox/', views.inbox_details, name='inbox'),
    path('inbox/<str:username>/', views.inbox_details, name='inbox_details'),

    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('contact/', views.contact, name='contact'),
    path('appointment/', views.appointment, name='appointment'),


]