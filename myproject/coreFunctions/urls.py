
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


]