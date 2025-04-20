from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def access_granted_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect('authUser:loginUser') 

        # Redirect if profile not completed
        if not user.profile_completed:
            return redirect('complete-profile')

        # After completing profile, route based on user_type
        if not user.status_verification:
            return redirect(reverse('authUser:profile_verification_in_progress'))

        return view_func(request, *args, **kwargs)

    return _wrapped_view
