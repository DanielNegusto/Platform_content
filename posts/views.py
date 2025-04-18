import stripe
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import Subscription
from .models import Post, Category
from .forms import PostForm

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class PostListView(ListView):
    model = Post
    template_name = "home.html"
    context_object_name = "posts"

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация только одобренных постов
        queryset = queryset.filter(moderation_status=Post.APPROVED)

        # Фильтрация по категориям
        categories = self.request.GET.getlist("categories")
        if categories:
            queryset = queryset.filter(categories__slug__in=categories).distinct()

        # Фильтрация по статусу
        status_filter = self.request.GET.get("status", "free")
        if status_filter == "paid":
            queryset = queryset.filter(status="paid")
        elif status_filter == "free":
            queryset = queryset.filter(status="free")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class PostCreateView(View):
    template_name = "post_form.html"

    def get(self, request):
        form = PostForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            new_category = form.cleaned_data.get("new_category")
            if new_category:
                slug = new_category.lower().replace(" ", "-")
                category, created = Category.objects.get_or_create(
                    name=new_category, slug=slug
                )
                post.categories.add(category)
            else:
                for category in form.cleaned_data["categories"]:
                    post.categories.add(category)

            return redirect("user_posts")

        return render(request, self.template_name, {"form": form})


class PostDetailView(DetailView):
    model = Post
    template_name = "post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            has_access = (
                self.object.status == "free"
                or self.object.author == user
                or Subscription.objects.filter(
                    user=user, subscribed_to=self.object.author
                ).exists()
                or user.is_staff
            )
        else:
            has_access = self.object.status == "free"

        context["has_access"] = has_access
        return context


class UserPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "user_posts.html"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


class PostUpdateView(View):
    template_name = "post_form.html"

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        form = PostForm(instance=post)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post.moderation_status = Post.PENDING
            form.save()
            return redirect("user_posts")
        return render(request, self.template_name, {"form": form})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "confirm_delete.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy("user_posts")
