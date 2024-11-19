from django.contrib import admin
from .models import User , VetProfile , PetOwnerProfile
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'gender', 'user_type')
admin.site.register(User, UserAdmin)


class VetAdmin(admin.ModelAdmin):
    list_display = ('user','clinic_name')
admin.site.register(VetProfile, VetAdmin)


admin.site.register(PetOwnerProfile)