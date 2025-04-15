from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Post, Category, Comment, ReplyComment, ChatMessage
from django.utils.text import slugify
from django.utils.timesince import timesince
from django.db.models import Q
from authUser.models import User, PetOwnerProfile
from django.db import models  # Add this import



# Create your views here.

@login_required(login_url='authUser:register')
def index(request):

    if request.user.user_type == 'vet' and request.user.profile_completed and not request.user.status_verification:
        # Redirect to a verification in progress page
        return redirect('authUser:profile_verification_in_progress') 
    
    # Normal feed logic (if the profile is verified)
    posts = Post.objects.all()
    categories = Category.objects.all()
    user_profile = PetOwnerProfile.objects.get(user=request.user)
    pets = user_profile.pets.all()  # Related name from your Pet model
    context = {
        'posts': posts,
        'categories': categories,
        'pets': pets
    }
    
    return render(request, 'coreFunctions/index.html', context)


from django.shortcuts import render, get_object_or_404
from .models import Post, Comment, ReplyComment

def post_detail(request, slug):
    # Get active post or 404
    post = get_object_or_404(Post, slug=slug, active=True)
    
    # Get active comments with their active replies
    comments = post.comments.filter(active=True).prefetch_related(
        models.Prefetch('replies', 
                       queryset=ReplyComment.objects.filter(active=True),
                       to_attr='active_replies')
    )
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'coreFunctions/post_detail.html', context)



def home(request):
    return render(request, 'coreFunctions/landing.html')

def about(request):
    return render(request, 'coreFunctions/about.html')

def community(request):
    return render(request, 'coreFunctions/community.html')

def contact(request):
    return render(request, 'coreFunctions/contact.html')

def appointment(request):
    return render(request, 'coreFunctions/appointment.html')


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


@login_required
def inbox_details(request, username=None):
    sender = request.user
    receiver = None
    messages_detail = None

    if username:
        receiver = get_object_or_404(User, username=username)
        # Fetch conversation between sender and receiver, ordered by date
        messages_detail = ChatMessage.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).order_by("date")
        # Mark received messages as read
        messages_detail.filter(receiver=sender).update(is_read=True)

    # Get recent conversations for sidebar
    recent_messages = ChatMessage.objects.filter(
        Q(sender=sender) | Q(receiver=sender)
    ).order_by("-date")

    # Organize conversations by partner, keeping the latest message
    conversation_partners = {}
    for message in recent_messages:
        partner = message.sender if message.sender != sender else message.receiver
        if partner.id not in conversation_partners:
            conversation_partners[partner.id] = message

    context = {
        "message_detail": messages_detail,
        "receiver": receiver,
        "message_list": conversation_partners.values(),
    }
    return render(request, 'chat/inbox_detail.html', context)


