from django.db import models
# from django.contrib.auth.models import User # Importing the User model for ForeignKey relation
from authUser.models import User, user_directory_path
from shortuuid.django_fields import ShortUUIDField
from django.utils.text import slugify
import shortuuid


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:  # Check if slug is empty or None
            uuid_key = shortuuid.uuid()  # Generate a short UUID
            uniqueid = uuid_key[:2]  # Use the first 2 characters
            self.slug = slugify(self.name) + '-' + str(uniqueid.lower())  # Create unique slug
        super(Category, self).save(*args, **kwargs)
    


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True, null=True) 
    image = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    video = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    pid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefgijklmnopqrstuvwxyz')
    likes = models.ManyToManyField(User, blank=True, related_name="likes")
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug is None:  # Check if slug is empty or None
            uuid_key = shortuuid.uuid()  # Generate a short UUID
            uniqueid = uuid_key[:2]  # Get the first 2 characters of the UUID
            self.slug = slugify(self.user.username) + '-' + str(uniqueid.lower())  # Create slug
        super(Post, self).save(*args, **kwargs)  # Call the original save method


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, blank=True, related_name="comment_likes")
    cid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    def __str__(self):
        return f'Comment on {self.post}: {self.comment[:50]}'

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def comment_replies(self):
        comment_replies = ReplyComment.objects.filter(comment=self)
        return comment_replies


class ReplyComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reply_user")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")
    reply = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    cid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    def __str__(self):
        return str(self.comment)

    class Meta:
        verbose_name = 'Reply Comment'
        verbose_name_plural = 'Reply Comments'


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_user")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="receiver")

    message = models.CharField(max_length=1000)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    mid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    # def __str__(self):
    #     return self.sender