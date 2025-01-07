from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Post, Category, Comment, ReplyComment
from django.utils.text import slugify
import shortuuid
from django.utils.timesince import timesince


# Create your views here.

@login_required(login_url='authUser:register')
def index(request):

    if request.user.user_type == 'vet' and request.user.profile_completed and not request.user.status_verification:
        # Redirect to a verification in progress page
        return redirect('authUser:profile_verification_in_progress') 
    
    # Normal feed logic (if the profile is verified)
    posts = Post.objects.all()
    categories = Category.objects.all()
    context = {
        'posts': posts,
        'categories': categories
    }
    
    return render(request, 'coreFunctions/index.html', context)



def create_post(request):
    if request.method == "POST":
        title = request.POST.get("title")
        category = request.POST.get("category")#outputs 1 as the html has category id in its value
        body = request.POST.get("body")
        image = request.FILES.get("image")

        uid_key = shortuuid.uuid()
        uniqueid = uid_key[:4]
        
        category = get_object_or_404(Category, id=category)  # retrieve the category instance

        if title:
            post = Post(  #can use create here too 
                title=title,
                image=image,
                category=category,
                body=body,
                user=request.user,
                slug=slugify(title) + "-" + str(uniqueid.lower())
            )
            post.save()
            return redirect("coreFunctions:feed")
            # Determine the profile image based on user type
            # if hasattr(request.user, 'VetProfile'):  # Check if the user has a vet profile
            #     profile_image = request.user.VetProfile.vet_image.url  # Get vet image
            # elif hasattr(request.user, 'PetOwnerProfile'):  # Check if the user has a pet profile
            #     profile_image = request.user.PetOwnerProfile.human_image.url  # Get human image
            # else:
            #     profile_image = None  # Fallback if neither profile exists

        #     return JsonResponse({
        #         "post": {
        #             "title": post.title,
        #             "category": post.category,
        #             "body": post.body,
        #             # "image": post.image.url,
        #             "username": post.user.username,
        #             # "profile_image": profile_image,
        #             "date": timesince(post.date),
        #             "id": post.id,
        #         },
        #     })
        # else:
        #     return JsonResponse({"error": "Image or title does not exist"})

    return JsonResponse({"data": "sent"})



#for liking logic
def like_post(request):
    id = request.GET['id']
    post = Post.objects.get(id=id)
    user = request.user
    liked = False

    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    data = {
        "bool": liked,
        "likes": post.likes.all().count()
    }

    return JsonResponse({"data": data})


#for cmt logic
def comment_post(request):
    id = request.GET['id']
    comment = request.GET['cmt']
    post = Post.objects.get(id=id)
    comment_count = Comment.objects.filter(post=post).count()
    user = request.user

    new_comment = Comment.objects.create(
        post=post,
        user=user,
        comment=comment
    )

    data = {
        "comment_count": comment_count + int(1),
        "comment": new_comment.comment,
        #profile imaging
        "date": timesince(new_comment.date),
        "comment_id": new_comment.id,
        "post_id": new_comment.post.id,
        "username": new_comment.user.username
    }

    return JsonResponse({"data": data})


#for liking the cmt logic
def comment_like(request):
    id = request.GET['id']
    comment = Comment.objects.get(id=id)
    user = request.user
    liked = False

    if user in comment.likes.all():
        comment.likes.remove(user)
        liked = False
    else:
        comment.likes.add(user)
        liked = True

    data = {
        "bool": liked,
        "likes": comment.likes.all().count()
    }

    return JsonResponse({"data": data})


def comment_reply(request):
    id = request.GET['id']
    reply = request.GET['reply']

    comment = Comment.objects.get(id=id)
    user = request.user

    new_reply = ReplyComment.objects.create(
        comment=comment,
        user=user,
        reply=reply
    )
    
    data = {
        "bool": True,
        "reply": new_reply.reply,
        #profile imaging
        "date": timesince(new_reply.date),
        "reply_id": new_reply.id,
        "post_id": new_reply.comment.post.id,
        "username": new_reply.user.username
    }

    return JsonResponse({"data": data})

    
