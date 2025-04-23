from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('django_admin:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper