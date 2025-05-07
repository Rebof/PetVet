from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from .models import VetProfile, PetOwnerProfile, Pet, Review
from django.contrib.auth.decorators import login_required
from coreFunctions.models import Post, Comment, ReplyComment
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.crypto import get_random_string
from django.urls import reverse
from appointment.models import Appointment
import re

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
            new_password = form.cleaned_data.get('new_password1')

            if not validate_password_strength(new_password):
                messages.error(request, 'Password must be at least 8 characters long, include at least one uppercase letter, one number, and one special character.')
                return redirect('authUser:account_settings')

            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('authUser:account_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('authUser:account_settings')

def validate_password_strength(password):
    """Validates that the password meets the required strength."""
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        return False
    return True


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
                return redirect('authUser:loginUser')
            else:
                messages.error(request, 'Incorrect password. Account deletion failed.')
        else:
            messages.error(request, 'Email does not match your account. Deletion failed.')
    
    return redirect('authUser:account_settings')


def forgot_password(request):
    """View for initiating password reset process."""
    template_name = 'authUser/forgot_passwordunauth.html'
    if request.user.is_authenticated:
        template_name = 'authUser/forgot_password.html'

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
            message = (
    f"Hello {user.full_name},\n\n"
    f"We received a request to reset your password.\n\n"
    f"Please click the link below to reset your password:\n"
    f"{reset_link}\n\n"
    f"If you did not request a password reset, please ignore this email.\n\n"
    f"Best regards,\n"
    f"The PetVet Team"
)
            # Send email
            send_mail(
                'PetVet - Password Reset',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

        except User.DoesNotExist:
            # Do not reveal user existence for security
            pass
        
        messages.success(request, 'If your email exists in our system, you will receive a password reset link.')

    return render(request, template_name)


def reset_password(request, token):
    """View for resetting password using token."""
    try:
        user = User.objects.get(otp=token)
        
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')

            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif not validate_password_strength(password1):
                messages.error(request, 'Password must be at least 8 characters long, include at least one uppercase letter, one number, and one special character.')
            else:
                # Set new password
                user.set_password(password1)
                # Clear the token
                user.otp = None
                user.save()
                
                messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
                return redirect('authUser:loginUser')
        
        return render(request, 'authUser/reset_password.html')
    
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('authUser:loginUser')


def RegisterView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered!")
        return redirect("coreFunctions:index")

    if request.method == "POST":
        # Extract data manually from request.POST
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender")
        user_type = request.POST.get("user_type")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        
        # Basic validation
        errors = {}
        
        if not full_name:
            errors["full_name"] = "Full name is required."
        
        if not email:
            errors["email"] = "Email is required."
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Email already exists."
            
        if not username:
            errors["username"] = "Username is required."
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Username already exists."
            
        if not phone:
            errors["phone"] = "Phone number is required."
            
        if not gender:
            errors["gender"] = "Gender is required."
            
        if not user_type:
            errors["user_type"] = "User type is required."
            
        if not password1:
            errors["password1"] = "Password is required."
            
        if not password2:
            errors["password2"] = "Password confirmation is required."
        elif password1 != password2:
            errors["password2"] = "Passwords do not match."
            
        # If there are errors, return them to the template
        if errors:
            for field, error in errors.items():
                messages.error(request, error)
            return render(request, "authUser/register.html", {"errors": errors})
        
        # Create user
        user = User(
            full_name=full_name,
            email=email,
            username=username,
            phone=phone,
            gender=gender,
            user_type=user_type,
        )
        user.set_password(password1)
        user.otp = str(random.randint(100000, 999999))
        user.save()

        # Send OTP email for pet_owner users
        if user_type == "pet_owner":
            subject = "Your OTP for Verification"
            message = (
    f"Hello {full_name},\n\n"
    f"Thank you for registering with PetVet!\n\n"
    f"Your One-Time Password (OTP) for verification is: {user.otp}\n\n"
    f"Please enter this OTP to complete your registration.\n\n"
    f"If you did not request this, please ignore this message.\n\n"
    f"Best regards,\n"
    f"The PetVet Team"
)
            send_mail(
                subject,    
                message,
                settings.DEFAULT_FROM_EMAIL, 
                [email],
                fail_silently=False,
            )
            messages.info(request, "An OTP has been sent to your email. Please verify to proceed.")
        
        user = authenticate(email=email, password=password1)

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

    return render(request, "authUser/register.html")



def LoginView(request):
    if request.user.is_authenticated:
        return redirect("coreFunctions:index")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        
        if user is not None:
            # If authentication is successful
            login(request, user)
            
            # Redirect to complete-profile if the profile is incomplete
            if not user.profile_completed: 
                # print("redirect bhayo")
                return redirect("complete-profile")
            
            return redirect("coreFunctions:index")
        else:
            # If authentication fails
            messages.error(request, "Invalid username or password")
            return redirect("authUser:loginUser")

    return render(request, "authUser/register.html")



def LogoutView(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("authUser:loginUser")


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
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to complete your profile.")
        return redirect('authUser:loginUser')
    
    try:
        if request.user.user_type == 'vet':
            profile = VetProfile.objects.get(user=request.user)
            profile_type = 'vet'
        elif request.user.user_type == 'pet_owner':
            profile = PetOwnerProfile.objects.get(user=request.user)
            profile_type = 'pet_owner'
        else:
            messages.error(request, "Invalid user type.")
            return redirect('coreFunctions:index')
    except (VetProfile.DoesNotExist, PetOwnerProfile.DoesNotExist):
        messages.error(request, "Profile not found. Please contact support.")
        return redirect('coreFunctions:index')
    
    errors = {}
    
    if request.method == 'POST':
        # Common fields for both profiles
        country = request.POST.get('country', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        use_default_image = request.POST.get('use_default_image') == 'on'
        
        # Validate common fields
        if not country:
            errors['country'] = "Country is required."
        if not city:
            errors['city'] = "City is required."
        if len(address) > 500:
            errors['address'] = "Address cannot exceed 500 characters."
        
        # Profile-specific validation
        if profile_type == 'pet_owner':
            bio = request.POST.get('bio', '').strip()
            pets_owned = request.POST.get('pets_owned', '0').strip()
            
            try:
                pets_owned = int(pets_owned)
                if pets_owned < 0 or pets_owned > 20:
                    errors['pets_owned'] = "Please enter a valid number between 0 and 20."
            except ValueError:
                errors['pets_owned'] = "Please enter a valid number."
            
            if len(bio) > 1000:
                errors['bio'] = "Bio cannot exceed 1000 characters."
                
        elif profile_type == 'vet':
            summary = request.POST.get('summary', '').strip()
            clinic_name = request.POST.get('clinic_name', '').strip()
            specialization = request.POST.get('specialization', '').strip()
            experience_years = request.POST.get('experience_years', '0').strip()
            license_number = request.POST.get('license_number', '').strip()
            
            if not clinic_name:
                errors['clinic_name'] = "Clinic name is required."
            elif len(clinic_name) > 100:
                errors['clinic_name'] = "Clinic name cannot exceed 100 characters."
                
            if not license_number:
                errors['license_number'] = "License number is required."
            elif len(license_number) > 50:
                errors['license_number'] = "License number cannot exceed 50 characters."
                
            try:
                experience_years = int(experience_years)
                if experience_years < 0 or experience_years > 60:
                    errors['experience_years'] = "Please enter valid experience years (0-60)."
            except ValueError:
                errors['experience_years'] = "Please enter a valid number."
            
            if len(summary) > 2000:
                errors['summary'] = "Summary cannot exceed 2000 characters."
            if len(specialization) > 100:
                errors['specialization'] = "Specialization cannot exceed 100 characters."
        
        # Image validation
        if not use_default_image:
            image_field = 'vet_image' if profile_type == 'vet' else 'human_image'
            uploaded_image = request.FILES.get(image_field)
            
            if uploaded_image:
                if uploaded_image.size > 5 * 1024 * 1024:  # 5MB limit
                    errors[image_field] = "Image size cannot exceed 5MB."
                elif not uploaded_image.content_type.startswith('image/'):
                    errors[image_field] = "Only image files are allowed."
        
        if not errors:
            try:
                # Update profile based on user type
                if profile_type == 'pet_owner':
                    profile.bio = bio
                    profile.pets_owned = pets_owned
                else:
                    profile.summary = summary
                    profile.clinic_name = clinic_name
                    profile.specialization = specialization
                    profile.experience_years = experience_years
                    profile.license_number = license_number
                
                # Update common fields
                profile.country = country
                profile.city = city
                profile.address = address
                
                # Handle profile image
                if use_default_image:
                    setattr(profile, f"{profile_type}_image", 'default.png')
                elif request.FILES.get(f"{profile_type}_image"):
                    setattr(profile, f"{profile_type}_image", request.FILES.get(f"{profile_type}_image"))
                
                profile.save()
                
                # Mark profile as completed
                request.user.profile_completed = True
                request.user.save()
                
                messages.success(request, "Profile successfully updated!")
                
                if not request.user.status_verification:
                    if request.user.user_type == "vet":
                        return redirect('authUser:profile_verification_in_progress')
                    else:
                        return redirect('authUser:verify_otp')
                
                return redirect('coreFunctions:index')
                
            except Exception as e:
                messages.error(request, f"An error occurred while saving your profile: {str(e)}")
                # Log the error here if you have logging set up
    
    # Prepare context for rendering the template
    context = {
        'profile': profile,
        'profile_type': profile_type,
        'errors': errors,
        'messages': messages.get_messages(request)
    }
    
    return render(request, 'authUser/profile.html', context)


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
    # If user is already verified, redirect them
    if request.user.status_verification:
        return redirect("coreFunctions:index")
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        if not entered_otp:
            messages.error(request, "Please enter the OTP")
            return render(request, 'authUser/verify_otp.html')

        # Compare the entered OTP
        if request.user.otp == entered_otp:
            request.user.status_verification = True
            request.user.otp = None  # Clear OTP after verification
            request.user.save()
            messages.success(request, "Your email has been verified successfully!")
            return redirect("coreFunctions:index")
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    
    # Handle GET request
    return render(request, 'authUser/verify_otp.html')
    

@login_required
def add_pet(request):
    errors = {}
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        species = request.POST.get('species', '').strip()
        breed = request.POST.get('breed', '').strip()
        age = request.POST.get('age', '').strip()
        color = request.POST.get('color', '').strip()
        weight = request.POST.get('weight', '').strip()
        vaccination_status = request.POST.get('vaccination_status', '').strip()
        allergies = request.POST.get('allergies', '').strip()
        medical_history = request.POST.get('medical_history', '').strip()
        pet_image = request.FILES.get('pet_image')

        # Validate required fields
        if not name:
            errors['name'] = "Pet name is required."
        if not species:
            errors['species'] = "Species is required."
        if not age:
            errors['age'] = "Age is required."
        elif not age.isdigit() or int(age) < 0 or int(age) > 50:
            errors['age'] = "Please enter a valid age (0-50)."
        if not color:
            errors['color'] = "Color is required."

        # Validate optional fields
        if weight and (not weight.replace('.', '').isdigit() or float(weight) <= 0):
            errors['weight'] = "Please enter a valid weight."
        
        # Validate image if provided
        if pet_image:
            if pet_image.size > 5 * 1024 * 1024:  # 5MB limit
                errors['pet_image'] = "Image size cannot exceed 5MB."
            elif not pet_image.content_type.startswith('image/'):
                errors['pet_image'] = "Only image files are allowed."

        if not errors:
            try:
                # Get owner profile
                owner_profile = PetOwnerProfile.objects.get(user=request.user)
                
                # Create pet with optional fields set to None if empty
                pet = Pet.objects.create(
                    owner=owner_profile,
                    name=name,
                    species=species,
                    breed=breed if breed else None,
                    age=age,
                    color=color,
                    weight=float(weight) if weight else None,
                    vaccination_status=vaccination_status if vaccination_status else None,
                    allergies=allergies if allergies else None,
                    medical_history=medical_history if medical_history else None,
                    pet_image=pet_image if pet_image else None
                )
                
                messages.success(request, f"{pet.name} has been successfully added to your pets!")
                return redirect('authUser:add_pet') 
                
            except PetOwnerProfile.DoesNotExist:
                messages.error(request, "You need to complete your profile before adding pets.")
                return redirect('authUser:complete_profile')
            except Exception as e:
                messages.error(request, f"An error occurred while adding your pet: {str(e)}")
        else:
            # Store the form data to repopulate the form
            request.session['pet_form_data'] = {
                'name': name,
                'species': species,
                'breed': breed,
                'age': age,
                'color': color,
                'weight': weight,
                'vaccination_status': vaccination_status,
                'allergies': allergies,
                'medical_history': medical_history
            }
            
            for field, error in errors.items():
                messages.error(request, error)
    
    # Check for saved form data in session
    form_data = request.session.pop('pet_form_data', None)
    context = {'form_data': form_data} if form_data else {}
    
    return render(request, 'authUser/add_pet.html', context)


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
        errors = {}
        
        # Get form data
        name = request.POST.get('name', '').strip()
        species = request.POST.get('species', '').strip()
        breed = request.POST.get('breed', '').strip()
        age = request.POST.get('age', '').strip()
        color = request.POST.get('color', '').strip()
        weight = request.POST.get('weight', '').strip()
        vaccination_status = request.POST.get('vaccination_status', '').strip()
        allergies = request.POST.get('allergies', '').strip()
        medical_history = request.POST.get('medical_history', '').strip()
        pet_image = request.FILES.get('pet_image')

        # Validate required fields
        if not name:
            errors['name'] = "Pet name is required."
        if not species:
            errors['species'] = "Species is required."
        elif species not in [choice[0] for choice in species_choices]:
            errors['species'] = "Please select a valid species."
        if not age:
            errors['age'] = "Age is required."
        elif not age.isdigit() or int(age) < 0 or int(age) > 50:
            errors['age'] = "Please enter a valid age (0-50)."
        if not color:
            errors['color'] = "Color is required."
        if not breed:  # Add breed validation if it's required
            errors['breed'] = "Breed is required."

        # Validate optional fields
        if weight and (not weight.replace('.', '').isdigit() or float(weight) <= 0):
            errors['weight'] = "Please enter a valid weight."
        
        # Validate image if provided
        if pet_image:
            if pet_image.size > 5 * 1024 * 1024:  # 5MB limit
                errors['pet_image'] = "Image size cannot exceed 5MB."
            elif not pet_image.content_type.startswith('image/'):
                errors['pet_image'] = "Only image files are allowed."

        if not errors:
            try:
                # Update pet information
                pet.name = name
                pet.species = species
                pet.breed = breed  # Don't set to None if it's required
                pet.age = age
                pet.color = color
                pet.weight = float(weight) if weight else None
                pet.vaccination_status = vaccination_status if vaccination_status else None
                pet.allergies = allergies if allergies else None
                pet.medical_history = medical_history if medical_history else None
                
                if pet_image:
                    pet.pet_image = pet_image
                
                pet.save()
                messages.success(request, f"{pet.name}'s profile has been updated successfully!")
                return redirect('authUser:pet_profile', pet_id=pet.id)
                
            except Exception as e:
                messages.error(request, f"An error occurred while updating the pet profile: {str(e)}")
        else:
            # Store the current valid values to repopulate the form
            pet.name = name
            pet.species = species
            pet.breed = breed  # Keep the breed value
            pet.age = age
            pet.color = color
            if weight and weight.replace('.', '').isdigit():
                pet.weight = float(weight)
            pet.vaccination_status = vaccination_status
            pet.allergies = allergies
            pet.medical_history = medical_history
            
            for field, error in errors.items():
                messages.error(request, error)

    context = {
        'pet': pet,
        'species_choices': species_choices,
    }
    return render(request, 'authUser/pet_profile.html', context)



@login_required
def review_vet(request, appointment_id):
    """View for reviewing a veterinarian after an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if the user is authorized to review this appointment
    if request.user != appointment.pet_owner.user:
        return HttpResponseForbidden("Only the pet owner can review this appointment")
    
    # Check if the appointment is completed and paid
    if appointment.status != 'completed' or appointment.payment_status != 'paid':
        messages.error(request, "You can only review completed and paid appointments")
        return redirect('appointment:appointment_detail', appointment_id=appointment.id)
    
    # Check if the user has already reviewed this appointment
    existing_review = Review.objects.filter(
        vet=appointment.vet,
        reviewer=request.user,
        appointment=appointment
    ).first()
    
    if existing_review:
        messages.info(request, "You have already reviewed this appointment")
        return redirect('appointment:appointment_detail', appointment_id=appointment.id)
    
    if request.method == 'POST':
        # Process the review submission
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        
        # Create the review
        review = Review.objects.create(
            vet=appointment.vet,
            reviewer=request.user,
            rating=rating,
            comment=comment,
            appointment=appointment
        )
        
        messages.success(request, "Thank you for your review!")
        return redirect('appointment:appointment_detail', appointment_id=appointment.id)
    
    context = {
        'appointment': appointment
    }
    return render(request, 'appointment/review_vet.html', context)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


@login_required
def delete_pet(request, pk):
    pet = get_object_or_404(Pet, id=pk, owner__user=request.user)
    if request.method == 'POST':
        pet_name = pet.name
        pet.delete()
        messages.success(request, f"{pet_name} has been removed from your profile.")
        return redirect('authUser:add_pet')
    raise Http404("Invalid request method")