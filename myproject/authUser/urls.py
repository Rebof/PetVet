
from django.urls import path

from . import views
app_name = "authUser"

urlpatterns = [
    path("register", views.RegisterView ,name="register"),
    path('login/', views.LoginView, name='loginUser'),  
    path('logout/', views.LogoutView, name='logoutUser'),
    path('user-info/', views.user_info, name='user-info'),

    path('profile-verification-in-progress/', views.profile_verification_in_progress, name='profile_verification_in_progress'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('add/', views.add_pet, name='add_pet'),
    path('pet/<int:pet_id>/', views.pet_profile, name='pet_profile'),
    # path('pet/<int:pk>/update/', views.update_pet, name='update_pet'),
    path('pet/<int:pk>/delete/', views.delete_pet, name='delete_pet'),
]