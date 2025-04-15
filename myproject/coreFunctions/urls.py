
from django.urls import path

from . import views
app_name = "coreFunctions"

urlpatterns = [
    path("", views.index, name="feed"),


    path("create-post/", views.create_post, name="create-post"),
    path("like-post/", views.like_post, name="like-post"),
    path("comment-post/", views.comment_post, name="comment-post"),
    path("comment-like/", views.comment_like, name="comment-like"),
    path("comment-reply/", views.comment_reply, name="comment-reply"),

    path('post/<str:slug>/', views.post_detail, name='post-detail'),

    # path("chat/inbox/", views.inbox_detail, name="inbox_detail"),
    # path("chat/inbox/<str:username>/", views.inbox_details, name="inbox_details"),

    path('inbox/', views.inbox_details, name='inbox'),
    path('inbox/<str:username>/', views.inbox_details, name='inbox_details'),

    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('contact/', views.contact, name='contact'),
    path('appointment/', views.appointment, name='appointment'),


]