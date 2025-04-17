
from django.urls import path

from . import views
app_name = "authUser"

urlpatterns = [
    path("register", views.RegisterView ,name="register"),
    path('login/', views.LoginView, name='loginUser'),  
    path('logout/', views.LogoutView, name='logoutUser'),
    path('profile-page/', views.user_info, name='user-info'),
    path('profile/<int:user_id>/', views.user_info, name='user_profile'),  # For other users

    path('profile-verification-in-progress/', views.profile_verification_in_progress, name='profile_verification_in_progress'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('add/', views.add_pet, name='add_pet'),
    path('pet/<int:pet_id>/', views.pet_profile, name='pet_profile'),
    # path('pet/<int:pk>/update/', views.update_pet, name='update_pet'),
    path('pet/<int:pk>/delete/', views.delete_pet, name='delete_pet'),

    

    path('settings/', views.account_settings, name='account_settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Account Deletion
    path('delete-account/', views.delete_account, name='delete_account'),
]