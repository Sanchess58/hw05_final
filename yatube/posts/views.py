from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator

COUNT_LINE = 10
COUNT_PAGE = 10


@cache_page(20, key_prefix="index_page")
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.select_related("author", "group")
    description = "Последние обновления на сайте"
    is_index = True
    context = {
        "description": description,
        "is_index": is_index,
        "page_obj": paginator(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("author")
    context = {"group": group, "page_obj": paginator(request, post_list)}
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    check = author != request.user
    following = False
    if request.user.is_authenticated and check:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    post_list = (
        author.posts.
        select_related("author", "group")
    )
    context = {
        "author": author,
        "page_obj": paginator(request, post_list),
        "following": following,
        "check": check,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form_comment = CommentForm(
        request.POST or None
    )
    context = {
        "post": post,
        "form": form_comment,
        "comments": comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = "posts/create_post.html"
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None,)
        context = {"form": form}
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", request.user)
        return render(request, template, context)
    form = PostForm()
    context = {"form": form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = "posts/create_post.html"
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    if request.method == "POST":
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post,
        )
        context = {
            "form": form,
            "is_edit": is_edit,
        }
        if form.is_valid():
            form.save()
            return redirect("posts:post_detail", post_id)
        return render(request, template, context)
    form = PostForm(instance=post)
    context = {
        "form": form,
        "is_edit": is_edit,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {"page_obj": paginator(request, post_list)}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if author != request.user and not following:
        Follow.objects.create(
            user=request.user,
            author=author
        )
        return redirect("posts:follow_index")
    return redirect("posts:index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    print(author.following.select_related("user", "author"))
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username)
