
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from authUser.views import complete_profile


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("coreFunctions.urls")),
    path("user/", include("authUser.urls")),
    path("django-admin/", include("django_admin.urls")),
    path("complete-profile/", complete_profile, name="complete-profile"),
    path("appointment/", include("appointment.urls")),
    # path('verify-otp/', VerifyOTPView, name='verify-otp'), 

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)