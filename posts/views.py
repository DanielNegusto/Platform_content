import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import Subscription
from .models import Post, Category
from .forms import PostForm

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class PostListView(ListView):
    model = Post
    template_name = 'home.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по категориям
        categories = self.request.GET.getlist('categories')  # Получаем список выбранных категорий
        if categories:
            queryset = queryset.filter(categories__slug__in=categories).distinct()  # Фильтруем по выбранным категориям

        # Фильтрация по статусу
        status_filter = self.request.GET.get('status', 'free')  # Устанавливаем 'free' как значение по умолчанию
        if status_filter == 'paid':
            queryset = queryset.filter(status='paid')  # Фильтруем только платные посты
        elif status_filter == 'free':
            queryset = queryset.filter(status='free')  # Фильтруем только бесплатные посты
        # Если status_filter пустой или не указан, по умолчанию будет 'free'

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()  # Передаем категории в контекст
        return context


class PostCreateView(View):
    template_name = 'post_form.html'

    def get(self, request):
        form = PostForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Устанавливаем автора поста
            post.save()  # Сначала сохраняем пост, чтобы получить id

            # Проверка и создание новой категории
            new_category = form.cleaned_data.get('new_category')
            if new_category:
                slug = new_category.lower().replace(' ', '-')
                category, created = Category.objects.get_or_create(name=new_category, slug=slug)
                post.categories.add(category)  # Добавляем новую категорию к посту
            else:
                # Добавляем существующие категории, если новая не введена
                for category in form.cleaned_data['categories']:
                    post.categories.add(category)

            return redirect('user_posts')  # Перенаправление на список постов или другую страницу

        return render(request, self.template_name, {'form': form})


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Проверяем, имеет ли пользователь доступ к посту
        if user.is_authenticated:
            # Проверяем, есть ли подписка на автора
            has_access = (self.object.status == 'free' or
                           self.object.author == user or
                           Subscription.objects.filter(user=user, subscribed_to=self.object.author).exists())
        else:
            # Неавторизованные пользователи могут видеть только бесплатные посты
            has_access = self.object.status == 'free'

        context['has_access'] = has_access
        return context


class UserPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'user_posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


class PostUpdateView(View):
    template_name = 'post_form.html'

    def get(self, request, pk):
        post = Post.objects.get(pk=pk)
        form = PostForm(instance=post)
        return render(request, self.template_name, {'form': form})

    def post(self, request, pk):
        post = Post.objects.get(pk=pk)
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('user_posts')  # Перенаправление на список постов или другую страницу
        return render(request, self.template_name, {'form': form})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'confirm_delete.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('user_posts')
