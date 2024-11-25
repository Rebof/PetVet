from django.urls import path
from . import views

app_name = "django_admin"
urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),  # Admin login route
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:vet_id>/', views.approve_vet, name='approve_vet'),
    path('decline/<int:vet_id>/', views.decline_vet, name='decline_vet'),
    path('logout/', views.admin_logout, name='admin_logout'),
]
