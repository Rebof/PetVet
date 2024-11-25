from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegistrationForm,VetProfileForm, PetOwnerProfileForm
from .models import VetProfile, PetOwnerProfile
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from coreFunctions.models import Post, Comment, ReplyComment





def RegisterView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered!")
        return redirect("coreFunctions:feed")

    form = UserRegistrationForm(request.POST or None)

    if form.is_valid():
        # Save the new user
        user = form.save(commit=False)
        user.set_password(form.cleaned_data.get("password1"))
        user.save()

        full_name = form.cleaned_data.get("full_name")
        email = form.cleaned_data.get("email")
        user_type = form.cleaned_data.get("user_type")

        # Authenticate the user
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
            if not user.profile_completed:  # Assume `profile_complete` is a boolean field in the user model
                return redirect("complete-profile")

            return redirect("coreFunctions:feed")
        else:
            messages.error(request, "There was an issue with your login. Please try again.")

    context = {'form': form}
    return render(request, "authUser/register.html", context)



def LoginView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect("coreFunctions:feed")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # If authentication is successful
            login(request, user)
            messages.success(request, "You are logged in")
            
            # Redirect to complete-profile if the profile is incomplete
            if not user.profile_completed:  # Assume `profile_complete` is a boolean field in the user model
                print("redirect bhayo")
                return redirect("complete-profile")
            
            return redirect("coreFunctions:feed")
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
def user_info(request):
    user = request.user

    # Fetch posts created by the user
    posts = Post.objects.filter(user=user)

    # Fetch comments made by the user
    comments = Comment.objects.filter(user=user)

    # Fetch reply comments made by the user
    reply_comments = ReplyComment.objects.filter(user=user)

    # Prepare context for rendering the template
    context = {
        'user': user,
        'profile': None,
        'posts': posts,  # Updated key for posts
        'comments': comments,  # Updated key for comments
        'reply_comments': reply_comments,  # Updated key for reply comments
    }

    # Determine user profile type and retrieve profile data
    if user.user_type == 'vet':
        profile = VetProfile.objects.get(user=user)
        context['profile'] = profile
    elif user.user_type == 'pet_owner':
        profile = PetOwnerProfile.objects.get(user=user)
        context['profile'] = profile

    return render(request, 'authUser/user_info.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import VetProfileForm, PetOwnerProfileForm
from .models import VetProfile, PetOwnerProfile

def complete_profile(request):
    # Determine which profile and form to use based on user type
    if request.user.user_type == 'vet':
        profile = VetProfile.objects.get(user=request.user)
        FormClass = VetProfileForm
    elif request.user.user_type == 'pet_owner':
        profile = PetOwnerProfile.objects.get(user=request.user)
        FormClass = PetOwnerProfileForm
    else:
        return redirect('/')  # Redirect for invalid user type

    # Handle form submission
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Mark profile as completed
            request.user.profile_completed = True
            request.user.save()
            messages.success(request, "Your profile has been completed successfully.")
            
            # Redirect to verification progress if vet profile is not verified yet
            if request.user.status_verification is False:
                return redirect('authUser:profile_verification_in_progress')  # Redirect to verification progress page

            return redirect('/')  # Redirect to home page if everything is fine
    else:
        form = FormClass(instance=profile)

    return render(request, 'authUser/profile.html', {'form': form})


def profile_verification_in_progress(request):
    # Check if the user is a vet and their profile is completed but not verified yet
    if request.user.user_type == 'vet' and request.user.profile_completed and not request.user.status_verification:
        return render(request, 'authUser/profile_verification_in_progress.html')
    # If the profile is verified, redirect to the feed page
    elif request.user.user_type == 'vet' and request.user.status_verification:
        return redirect("coreFunctions:feed")
    else:
        # If the user is not a vet or verification is not needed
        return redirect("coreFunctions:feed")
