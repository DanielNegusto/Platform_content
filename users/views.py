import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView
from django.urls import reverse_lazy

from posts.models import Post
from .tasks import send_code_email
from .forms import SignUpForm, UserProfileForm  # Предполагается, что у вас есть форма для регистрации
from .models import User, Subscription
from .services import generate_code

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'signup.html'
    success_url = reverse_lazy('confirmation')

    def form_valid(self, form):
        # Сохранение пользователя
        user = form.save(commit=False)
        confirmation_code = generate_code()
        user.checking_code = confirmation_code

        user.set_password(form.cleaned_data['password'])
        user.save()

        # Сохраняем номер телефона в сессии
        self.request.session['phone_number'] = user.phone_number

        # Отправка кода подтверждения
        send_code_email.delay(user.email, confirmation_code)

        messages.success(self.request, "Пожалуйста, проверьте свою почту для подтверждения регистрации.")
        return super().form_valid(form)


class CustomLoginView(View):
    def get(self, request):
        return render(request, 'login.html')  # Замените на ваш шаблон

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        user = authenticate(request, username=phone_number, password=password)

        if user is not None:
            login(request, user)
            return redirect('profile')  # Замените на ваш URL
        else:
            messages.error(request, 'Неверный номер телефона или пароль.')
            return render(request, 'login.html')


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()  # Получаем объект пользователя
        posts = Post.objects.filter(author=user)  # Получаем посты пользователя
        stripe_public_key = settings.STRIPE_TEST_PUBLIC_KEY  # Получаем публичный ключ Stripe

        # Проверка подписки
        is_subscribed = Subscription.objects.filter(user=self.request.user, subscribed_to=user).exists()
        # Подсчет подписчиков
        subscribers_count = user.subscribers.count()  # Используем правильное имя атрибута

        context['posts'] = posts
        context['stripe_public_key'] = stripe_public_key
        context['is_subscribed'] = is_subscribed  # Добавляем информацию о подписке
        context['subscribers_count'] = subscribers_count  # Добавляем количество подписчиков

        return context

    def get_object(self, queryset=None):
        email = self.kwargs.get('email')  # Получаем email из URL
        if email:  # Если email указан, ищем пользователя по email
            return get_object_or_404(User, email=email)
        return self.request.user


class EditProfileView(LoginRequiredMixin, View):
    template_name = 'edit_profile.html'

    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен.")
            return redirect('profile')
        return render(request, self.template_name, {'form': form})


class ConfirmationView(View):
    template_name = 'confirmation.html'

    def get(self, request):
        # Получаем номер телефона из сессии
        phone_number = request.session.get('phone_number')
        return render(request, self.template_name, {'phone_number': phone_number})

    def post(self, request):
        confirmation_code = request.POST.get('confirmation_code')

        # Получаем пользователя по номеру телефона из сессии
        phone_number = request.session.get('phone_number')
        user = get_object_or_404(User, phone_number=phone_number)

        # Проверяем проверочный код
        if user.checking_code == confirmation_code:
            user.is_active = True
            user.save()
            messages.success(request, "Ваш аккаунт активирован!")
            return redirect('login')
        else:
            messages.error(request, "Неверный код подтверждения.")

        return redirect('confirmation')


class CreateCheckoutSessionView(View):
    def post(self, request, user_id):
        user = User.objects.get(id=user_id)

        # Создайте сессию платежа для подписки
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'rub',  # Указываем рубли
                        'product_data': {
                            'name': f'Подписка для {user.email}',  # Название продукта
                        },
                        'unit_amount': 60000,  # Указываем цену в копейках (600 рублей = 60000 копеек)
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/users/success/'),  # Укажите URL для успешной оплаты
            cancel_url=request.build_absolute_uri('/users/cancel/'),  # Укажите URL для отмены
        )

        return JsonResponse({'id': session.id})


class SuccessView(View):
    def get(self, request):
        subscribed_to_id = request.GET.get('subscribed_to_id')
        user_id = request.GET.get('user_id')

        if not subscribed_to_id:
            return HttpResponse("Subscribed to ID not provided", status=400)

        subscribed_to = get_object_or_404(User, id=subscribed_to_id)
        user = get_object_or_404(User, id=user_id) or request.user

        # Создание записи в модели Subscription
        Subscription.objects.create(user=user, subscribed_to=subscribed_to)

        return render(request, 'success.html', {'subscribed_to': subscribed_to})


class ErrorView(View):
    def get(self, request):
        return render(request, 'error.html')
