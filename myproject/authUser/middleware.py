# middleware.py
from django.shortcuts import redirect

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Redirect to /complete-profile/ if profile is not completed
            if not request.user.profile_completed and not request.path.startswith('/complete-profile/'):
                return redirect('/complete-profile/')
        return self.get_response(request)
