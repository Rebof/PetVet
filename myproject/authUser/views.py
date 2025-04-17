from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from .forms import UserRegistrationForm,VetProfileForm, PetOwnerProfileForm
from .models import VetProfile, PetOwnerProfile, Pet
from django.contrib.auth.decorators import login_required
from coreFunctions.models import Post, Comment, ReplyComment
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.crypto import get_random_string
from django.urls import reverse


User = get_user_model()

@login_required
def account_settings(request):
    """View for displaying and handling account settings."""
    return render(request, 'authUser/settings.html')

@login_required
def change_password(request):
    """View for changing user password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('authUser:account_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('authUser:account_settings')

@login_required
def delete_account(request):
    """View for deleting user account."""
    if request.method == 'POST':
        email = request.POST.get('confirm_email')
        password = request.POST.get('confirm_password')
        
        # Verify user credentials
        if email == request.user.email:
            user = request.user
            if user.check_password(password):
                # Log the user out first
                logout(request)
                # Delete the user account
                user.delete()
                messages.success(request, 'Your account has been permanently deleted.')
                return redirect('authUser:login')
            else:
                messages.error(request, 'Incorrect password. Account deletion failed.')
        else:
            messages.error(request, 'Email does not match your account. Deletion failed.')
    
    return redirect('authUser:account_settings')

def forgot_password(request):
    """View for initiating password reset process."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = get_random_string(64)
            # Save token to user profile or a dedicated password reset model
            user.otp = token
            user.save()
            
            # Create reset link
            reset_link = request.build_absolute_uri(
                reverse('authUser:reset_password', kwargs={'token': token})
            )
            
            # Send email
            send_mail(
                'PetCare Connect - Password Reset',
                f'Click the following link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Password reset link has been sent to your email.')
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security reasons
            messages.success(request, 'If your email exists in our system, you will receive a password reset link.')
    
    return render(request, 'authUser/forgot_password.html')

def reset_password(request, token):
    """View for resetting password using token."""
    try:
        user = User.objects.get(otp=token)
        
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            
            if password1 == password2:
                # Set new password
                user.set_password(password1)
                # Clear the token
                user.otp = None
                user.save()
                
                messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
                return redirect('authUser:login')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'authUser/reset_password.html')
    
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('authUser:loginUser')


def RegisterView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered!")
        return redirect("coreFunctions:index")

    form = UserRegistrationForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data.get("password1"))
        user.otp = str(random.randint(100000, 999999))
        user.save()

        full_name = form.cleaned_data.get("full_name")
        email = form.cleaned_data.get("email")
        user_type = form.cleaned_data.get("user_type")

         # Send OTP email for pet_owner users
        if user_type == "pet_owner":
            subject = "Your OTP for Verification"
            message = f"Hi {full_name},\n\nYour OTP for verification is: {user.otp}.\nPlease enter this OTP to complete your registration."
            send_mail(
                subject,
                message,
                'no-reply@example.com', 
                [email],
                fail_silently=False,
            )
            messages.info(request, "An OTP has been sent to your email. Please verify to proceed.")

        
        user = authenticate(email=email, password=form.cleaned_data.get("password1"))

        if user is not None:
            login(request, user)

            # Create or update the user profile
            if user_type == 'vet':
                vet_profile, created = VetProfile.objects.get_or_create(user=user)
                vet_profile.full_name = full_name
                vet_profile.save()
            elif user_type == 'pet_owner':
                pet_profile, created = PetOwnerProfile.objects.get_or_create(user=user)
                pet_profile.full_name = full_name
                pet_profile.save()

            messages.success(request, f"Hi {full_name}, your account was created successfully.")
            
            # Redirect to complete-profile if the profile is incomplete
            if not user.profile_completed:  
                return redirect("complete-profile")

            return redirect("coreFunctions:index")
        else:
            messages.error(request, "There was an issue with your login. Please try again.")

    context = {'form': form}
    return render(request, "authUser/register.html", context)


def LoginView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect("coreFunctions:index")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # If authentication is successful
            login(request, user)
            messages.success(request, "You are logged in")
            
            # Redirect to complete-profile if the profile is incomplete
            if not user.profile_completed: 
                print("redirect bhayo")
                return redirect("complete-profile")
            
            return redirect("coreFunctions:index")
        else:
            # If authentication fails
            messages.error(request, "Invalid username or password")
            return redirect("authUser:register")

    return render(request, "authUser/register.html")



def LogoutView(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("authUser:register")




@login_required
def user_info(request, user_id=None):
    # If no user_id is provided, show the current user's profile
    if user_id is None:
        user = request.user
    else:
        user = get_object_or_404(User, id=user_id)
    
    # Get the profile based on user type
    if user.user_type == 'vet':
        profile = VetProfile.objects.get(user=user)
        profile_picture_field = 'vet_image'
    else:
        profile = PetOwnerProfile.objects.get(user=user)
        profile_picture_field = 'human_image'

    if request.method == 'POST' and request.user == user:
        # Handle profile update
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone = request.POST.get('phone', user.phone)
        user.gender = request.POST.get('gender', user.gender)
        
        if user.user_type == 'vet':
            profile.clinic_name = request.POST.get('clinic_name', profile.clinic_name)
            profile.specialization = request.POST.get('specialization', profile.specialization)
            profile.experience_years = request.POST.get('experience_years', profile.experience_years)
            profile.license_number = request.POST.get('license_number', profile.license_number)
            profile.summary = request.POST.get('summary', profile.summary)
        else:
            profile.bio = request.POST.get('bio', profile.bio)
            profile.pets_owned = request.POST.get('pets_owned', profile.pets_owned)
        
        profile.country = request.POST.get('country', profile.country)
        profile.city = request.POST.get('city', profile.city)
        profile.address = request.POST.get('address', profile.address)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            current_picture = getattr(profile, profile_picture_field)
            if current_picture:
                current_picture.delete()
            setattr(profile, profile_picture_field, request.FILES['profile_picture'])
        
        user.save()
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('authUser:user-info')

    # Fetch posts created by the user
    posts = Post.objects.filter(user=user)
    comments = Comment.objects.filter(user=user)
    reply_comments = ReplyComment.objects.filter(user=user)

    context = {
        'user': user,
        'profile': profile,
        'profile_picture_field': profile_picture_field,
        'posts': posts,
        'comments': comments,
        'reply_comments': reply_comments,
        'is_own_profile': (request.user == user),
    }

    return render(request, 'authUser/user_info.html', context)



def complete_profile(request):

    if request.user.user_type == 'vet':
        profile = VetProfile.objects.get(user=request.user)
        FormClass = VetProfileForm
    elif request.user.user_type == 'pet_owner':
        profile = PetOwnerProfile.objects.get(user=request.user)
        FormClass = PetOwnerProfileForm
    else:
        return redirect('/') 
    
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Mark profile as completed
            request.user.profile_completed = True
            request.user.save()
            messages.success(request, "Your profile has been completed successfully.")
            
            if request.user.status_verification is False:
                return redirect('authUser:profile_verification_in_progress')

            return redirect('/')  
    else:
        form = FormClass(instance=profile)

    return render(request, 'authUser/profile.html', {'form': form})


def profile_verification_in_progress(request):
    # Check if the user is a vet and their profile is completed but not verified yet
    if request.user.user_type == 'vet' and request.user.profile_completed and not request.user.status_verification:
        return render(request, 'authUser/profile_verification_in_progress.html')
    elif request.user.user_type == 'pet_owner' and request.user.profile_completed and not request.user.status_verification:
        return render(request, 'authUser/verify_otp.html')
    # If the profile is verified, redirect to the feed page
    elif request.user.user_type == 'vet' and request.user.status_verification:
        return redirect("coreFunctions:index")
    else:
        # If the user is not a vet or verification is not needed
        return redirect("coreFunctions:index")
    

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        # Compare the entered OTPs
        if request.user.otp == entered_otp:
            request.user.status_verification = True
            request.user.otp = ""  # Clear OTP 
            request.user.save()
            messages.success(request, "Your email has been verified successfully!")
            return redirect('coreFunctions:feed')  
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    
    
    return render(request, 'authUser/verify_otp.html')
    
@login_required
def add_pet(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        species = request.POST.get('species')
        breed = request.POST.get('breed')
        age = request.POST.get('age')
        color = request.POST.get('color')
        weight = request.POST.get('weight')
        vaccination_status = request.POST.get('vaccination_status')
        allergies = request.POST.get('allergies')
        medical_history = request.POST.get('medical_history')
        pet_image = request.FILES.get('pet_image')

        # Get the PetOwnerProfile linked to the current user
        try:
            owner_profile = PetOwnerProfile.objects.get(user=request.user)
        except PetOwnerProfile.DoesNotExist:
            # Handle case where the user is not a pet owner
            return redirect('coreFunctions:index')  # or any fallback

        # Create and save the pet instance
        pet = Pet.objects.create(
            owner=owner_profile,
            name=name,
            species=species,
            breed=breed,
            age=age,
            color=color,
            weight=weight if weight else None,
            vaccination_status=vaccination_status,
            allergies=allergies,
            medical_history=medical_history,
            pet_image=pet_image
        )

        return redirect('coreFunctions:index')  # Replace with the correct URL name for pet list

    return render(request, 'authUser/add_pet.html')

@login_required
def pet_profile(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner__user=request.user)
    species_choices = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('fish', 'Fish'),
        ('rabbit', 'Rabbit'),
        ('other', 'Other'),
    ]
    
    if request.method == 'POST':
        # Handle form submission for updating pet info
        pet.name = request.POST.get('name')
        pet.species = request.POST.get('species')
        pet.breed = request.POST.get('breed')
        pet.age = request.POST.get('age')
        pet.color = request.POST.get('color', '')
        
        # Handle optional fields
        weight = request.POST.get('weight')
        pet.weight = float(weight) if weight else None
        
        pet.vaccination_status = request.POST.get('vaccination_status', '')
        pet.allergies = request.POST.get('allergies', '')
        pet.medical_history = request.POST.get('medical_history', '')
        
        # Handle image upload
        if 'pet_image' in request.FILES:
            pet.pet_image = request.FILES['pet_image']
        
        try:
            pet.save()
            messages.success(request, f"{pet.name}'s profile has been updated successfully!")
            return redirect('pet_profile', pet_id=pet.id)
        except Exception as e:
            messages.error(request, f"Error updating pet profile: {str(e)}")
    
    context = {
        'pet': pet,
        'species_choices': species_choices,
    }
    return render(request, 'authUser/pet_profile.html', context)

@login_required
def delete_pet(request, pk):
    pet = get_object_or_404(Pet, id=pk, owner__user=request.user)
    if request.method == 'POST':
        pet_name = pet.name
        pet.delete()
        messages.success(request, f"{pet_name} has been removed from your profile.")
        return redirect('coreFunctions:index')  # Make sure this is your correct redirect target
    raise Http404("Invalid request method")