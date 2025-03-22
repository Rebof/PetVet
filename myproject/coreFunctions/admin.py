from django.contrib import admin
from coreFunctions.models import Post, Category, Comment, ReplyComment, ChatMessage
# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_editable = ['active']
    list_display = ['title', 'user', 'active']
    # prepopulated_fields = {'slug': ('title',)}

admin.site.register(Post, PostAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Category, CategoryAdmin)

class ChatMessageAdmin(admin.ModelAdmin):
    list_editable = ['message']
    list_display = ['sender', 'receiver', 'message', 'is_read']

admin.site.register(ChatMessage, ChatMessageAdmin)

admin.site.register(Comment)
admin.site.register(ReplyComment)
