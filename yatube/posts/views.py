from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .common import paginator_func
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_PER_PAGE = 10


def index(request):
    title = "Последние обновления на сайте"
    caption = "Последние обновления на сайте"

    post_list = Post.objects.select_related("group", "author").all()
    page_obj = paginator_func(request, post_list)
    context = {
        "page_obj": page_obj,
        "title": title,
        "caption": caption,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("author").all()
    page_obj = paginator_func(request, post_list)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("group").all()
    page_obj = paginator_func(request, post_list)
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists(),
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = CommentForm()
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("posts:post_detail", post_id=post.id)
    else:
        form = CommentForm()
    comments = post.comments.select_related("author").all()
    context = {
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(
            request.POST,
            files=request.FILES,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", username=post.author)
    else:
        form = PostForm()
    context = {
        "form": form,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post.pk)
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            form.save()
            return redirect("posts:post_detail", post.pk)
    else:
        form = PostForm(instance=post)
    is_edit = True
    context = {
        "post": post,
        "form": form,
        "is_edit": is_edit,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("posts:post_detail", post.pk)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related("author").filter(
        author__following__user=request.user
    )
    page_obj = paginator_func(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username=username)
