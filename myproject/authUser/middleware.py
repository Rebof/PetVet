from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
import traceback
from django.shortcuts import render
from django.http import HttpResponseServerError

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of paths that should bypass all checks
        allowed_paths = [
            '/complete-profile/',
            reverse('authUser:profile_verification_in_progress'),
            reverse('coreFunctions:home'),
            reverse('coreFunctions:appointment'),
            reverse('coreFunctions:community'),
            reverse('coreFunctions:about'),
            reverse('coreFunctions:contact'),
            reverse('authUser:loginUser'),
            reverse('authUser:logoutUser'),
            reverse('authUser:verify_otp'),
            reverse('authUser:forgot_password'),
        ]
        
        # Path prefixes that should always be accessible
        exempt_prefixes = (
            '/static/', 
            '/media/', 
            '/ws/', 
            '/api/',
            '/admin/',
        )

        user = request.user

        if not user.is_authenticated:
            return self.get_response(request)

        if user.is_superuser or user.is_staff:
            return self.get_response(request)

        # Bypass checks for allowed paths and exempt prefixes
        if request.path.startswith(exempt_prefixes) or (request.path in allowed_paths):
            return self.get_response(request)

        
        if not user.profile_completed:
            return redirect('complete-profile')

        # Step 2
        if not user.status_verification:
            if user.user_type == "vet":
                return redirect('authUser:profile_verification_in_progress')
            else:
                # Only redirect to OTP verification if user is pet_owner and not verified
                return redirect('authUser:verify_otp')


        return self.get_response(request)
    
class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)

            # You can handle 404 here if status_code is 404
            if response.status_code == 404:
                return render(request, 'error.html', status=404)

            return response

        except Exception as e:
            # You can log the error or email the admin here
            if settings.DEBUG:
                print(traceback.format_exc())
            return render(request, 'errors/404.html', {'error': str(e)}, status=404)