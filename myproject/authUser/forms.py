from django.contrib.auth.forms import UserCreationForm
from .models import VetProfile, PetOwnerProfile
from django import forms
from .models import User

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'username', 'phone', 'gender', 'user_type', 'password1', 'password2']


class PetOwnerProfileForm(forms.ModelForm):
    class Meta:
        model = PetOwnerProfile
        fields = [
            'bio', 
            'pets_owned', 
            'human_image', 
            'country', 
            'city', 
            'address', 
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a short bio'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter your address'}),
        }

class VetProfileForm(forms.ModelForm):
    class Meta:
        model = VetProfile
        fields = [ 
            'clinic_name', 
            'specialization', 
            'experience_years', 
            'license_number', 
            'vet_image', 
            'country', 
            'city', 
            'address', 
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={'placeholder': 'e.g., Small Animals, Exotics'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter your clinic address'}),
        }