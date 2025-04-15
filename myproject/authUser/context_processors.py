from .models import Pet

def user_pets(request):
    if request.user.is_authenticated and hasattr(request.user, 'petownerprofile'):
        pets = Pet.objects.filter(owner=request.user.petownerprofile)
        return {'pets': pets}
    return {'pets': []}


