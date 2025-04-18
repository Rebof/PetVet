from django.db import models


from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.utils.text import slugify
from PIL import Image
import shortuuid
from shortuuid.django_fields import ShortUUIDField


# Choices
USER_TYPE_CHOICES = (
    ('vet', 'Veterinarian'),
    ('pet_owner', 'Pet Owner'),
)

GENDER = (
    ("female", "Female"),
    ("male", "Male"),
)


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.user.id, ext)
    return 'user_{0}/{1}'.format(instance.user.id, filename)


# Custom User model with added user_type field
class User(AbstractUser):
    full_name = models.CharField(max_length=1000, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GENDER, null=True, blank=True)
    status_verification = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)  
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='pet_owner')
    
    otp = models.CharField(max_length=100, null=True, blank=True)
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return str(f'{self.username}')


# Profile for Veterinarians
class VetProfile(models.Model):
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clinic_name = models.CharField(max_length=1000, null=True, blank=True)
    summary = models.CharField(max_length=1000, null=True, blank=True)
    specialization = models.CharField(max_length=500, null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    license_number = models.CharField(max_length=100, null=True, blank=True)
    vet_image = models.ImageField(upload_to=user_directory_path, default="default.png", null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=1000, null=True, blank=True)
    verified = models.BooleanField(default=False)
    status_change = models.DateTimeField(null=True, blank=True)
    # blocked = models.ManyToManyField(User, blank=True, related_name="blocked")
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # Add slug field

    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 2)
        return 0
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug is None: 
            uuid_key = shortuuid.uuid()  # Generate a short UUID
            uniqueid = uuid_key[:2]  # Get the first 2 characters of the UUID
            self.slug = slugify(self.user.full_name) + '.' + str(uniqueid.lower())  
        super(VetProfile, self).save(*args, **kwargs)  # Call the original save method


    def __str__(self):
        return str(self.user.full_name if self.user.full_name else self.user.username)

class Review(models.Model):
    vet = models.ForeignKey(VetProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey('appointment.Appointment', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)

    def __str__(self):
        return f"Review by {self.reviewer} for {self.vet.user.username}"


# Profile for Pet Owners
class PetOwnerProfile(models.Model):
    pid = ShortUUIDField(length=7, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz123")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=100, null=True, blank=True)
    pets_owned = models.IntegerField(null=True, blank=True)  
    human_image = models.ImageField(upload_to=user_directory_path, default="default.png", null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=1000, null=True, blank=True)
    # blocked = models.ManyToManyField(User, blank=True, related_name="blocked")
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    verified = models.BooleanField(default=False)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    credit_balance = models.PositiveIntegerField(default=0)


    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug is None:  # Check if slug is empty or None
            uuid_key = shortuuid.uuid()  # Generate a short UUID
            uniqueid = uuid_key[:2]  # Get the first 2 characters of the UUID
            self.slug = slugify(self.user.full_name) + '.' + str(uniqueid.lower())  # Create slug
        super(PetOwnerProfile, self).save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return str(self.user.username)

class Pet(models.Model):
    owner = models.ForeignKey(PetOwnerProfile, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    species = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    pet_image = models.ImageField(upload_to='pet_images/', default="default-pet.png" ,null=True, blank=True)

    # Optional fields
    medical_history = models.TextField(null=True, blank=True)
    vaccination_status = models.CharField(max_length=200, null=True, blank=True)
    allergies = models.CharField(max_length=200, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  
    color = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.user.username})"


# Signal to create appropriate profile based on user_type
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'vet':
            VetProfile.objects.create(user=instance)
        elif instance.user_type == 'pet_owner':
            PetOwnerProfile.objects.create(user=instance)

def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 'vet':
        instance.vetprofile.save()
    elif instance.user_type == 'pet_owner':
        instance.petownerprofile.save()


# Connect signals to User model
post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
