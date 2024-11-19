from django.contrib import admin
from coreFunctions.models import Post, Category, Comment, ReplyComment
# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_editable = ['active']
    list_display = ['title', 'user', 'active']
    # prepopulated_fields = {'slug': ('title',)}

admin.site.register(Post, PostAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Category, CategoryAdmin)


admin.site.register(Comment)
admin.site.register(ReplyComment)
