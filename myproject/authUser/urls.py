
from django.urls import path

from . import views
app_name = "authUser"

urlpatterns = [
    path("register", views.RegisterView ,name="register"),
    path('login/', views.LoginView, name='loginUser'),  
    path('logout/', views.LogoutView, name='logoutUser'),
    # path('complete-profile/', views.complete_profile, name='complete-profile'),
    path('user-info/', views.user_info, name='user-info'),
    path('profile-verification-in-progress/', views.profile_verification_in_progress, name='profile_verification_in_progress'),

]