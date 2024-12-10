from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from authUser.models import VetProfile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages



def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('django_admin:admin_dashboard')  # Redirect to the admin dashboard or homepage
        else:
            messages.error(request, "Invalid email or password")
    return render(request, 'django_admin/login.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect('django_admin:admin_login')


from django.utils.timezone import now, timedelta

def admin_dashboard(request):
    # Get all vets pending approval
    pending_vets = VetProfile.objects.filter(user__status_verification=False,user__profile_completed=True ,user__user_type='vet')

    # Get recently approved vets (approved in the last 7 days)
    recently_approved_vets = VetProfile.objects.filter(
        user__status_verification=True,  
        status_change__gte=now() - timedelta(days=7)  # Filter by status_change
    )

    # Get recently declined vets (declined in the last 7 days)
    recently_declined_vets = VetProfile.objects.filter(
        user__status_verification=False, 
        status_change__gte=now() - timedelta(days=7)  # Filter by status_change
    )

    return render(request, 'django_admin/dashboard.html', {
        'pending_vets': pending_vets,
        'recently_approved_vets': recently_approved_vets,
        'recently_declined_vets': recently_declined_vets,
        'admin_user': request.user,
    })

def approve_vet(request, vet_id):
    vet_profile = get_object_or_404(VetProfile, id=vet_id)
    vet_user = vet_profile.user
    vet_user.status_verification = True  # Approve the vet
    vet_profile.status_change = now() 
    vet_user.save()
    vet_profile.save()
    return redirect('django_admin:admin_dashboard')

def decline_vet(request, vet_id):
    # Get the VetProfile object (which is related to the User)
    vet_profile = get_object_or_404(VetProfile, id=vet_id)
    
    vet_profile.user.profile_completed = False  # Set profile_completed to False in the User model
    vet_profile.user.save()  # Save the User model with updated field
    
    vet_profile.status_change = now()  # Track the time of the decline action
    
    # Save the changes to the VetProfile
    vet_profile.save()

    #vet_profile.delete()  # Delete the VetProfile record
    
    return redirect('django_admin:admin_dashboard')
