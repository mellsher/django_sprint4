from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.urls import reverse

from .models import Post, Category
from .forms import PostForm, CommentForm, RegistrationForm


def index(request):
    posts = Post.objects.select_related('category', 'location', 'author')
    posts = posts.filter(is_published=True, category__is_published=True, pub_date__lte=timezone.now())
    posts = posts.annotate(comment_count=Count('comments')).order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    # show unpublished/future posts to their author
    if request.user.is_authenticated:
        try:
            post = Post.objects.select_related('category', 'location', 'author').get(pk=post_id)
        except Post.DoesNotExist:
            post = None
    else:
        post = None

    if post is None:
        post = get_object_or_404(
            Post.objects.select_related('category', 'location', 'author'),
            pk=post_id,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    else:
        # if found by pk above but not visible to anonymous, ensure category published or owner
        if not (request.user == post.author or (post.is_published and post.pub_date <= timezone.now() and post.category.is_published)):
            post = get_object_or_404(
                Post.objects.select_related('category', 'location', 'author'),
                pk=post_id,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )

    comments = post.comments.select_related('author').order_by('created_at')
    form = CommentForm()
    context = {'post': post, 'comments': comments, 'form': form}
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)

    posts = category.posts.select_related('category', 'location', 'author')
    posts = posts.filter(is_published=True, pub_date__lte=timezone.now())
    posts = posts.annotate(comment_count=Count('comments')).order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'category': category, 'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


def profile(request, username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    if request.user.is_authenticated and request.user == user:
        posts = Post.objects.filter(author=user).select_related('category', 'location', 'author')
    else:
        posts = Post.objects.filter(author=user, is_published=True, pub_date__lte=timezone.now(), category__is_published=True).select_related('category', 'location', 'author')

    posts = posts.annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'profile_user': user, 'page_obj': page_obj, 'profile': user}
    return render(request, 'blog/profile.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(reverse('blog:profile', args=[request.user.username]))
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    # ensure unauthenticated users are redirected to login when attempting POST
    if not request.user.is_authenticated:
        from django.urls import reverse
        return redirect(f"{reverse('login')}?next={request.path}")

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        username = post.author.username
        post.delete()
        return redirect('blog:profile', username)

    # render confirmation using existing template without form in context
    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    from .models import Comment as CommentModel
    comment = get_object_or_404(CommentModel, pk=comment_id, post__id=post_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    from .models import Comment as CommentModel
    comment = get_object_or_404(CommentModel, pk=comment_id, post__id=post_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    # render confirmation using existing template without form in context
    return render(request, 'blog/comment.html', {'comment': comment})


@login_required
def edit_profile(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if request.method == 'POST':
        from .forms import ProfileForm
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', request.user.username)
    else:
        from .forms import ProfileForm
        form = ProfileForm(instance=request.user)
    return render(request, 'blog/edit_profile.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:profile', user.username)
    else:
        form = RegistrationForm()
    return render(request, 'registration/registration_form.html', {'form': form})
