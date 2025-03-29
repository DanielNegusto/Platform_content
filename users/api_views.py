from django.conf import settings
from django.http import JsonResponse
from rest_framework import generics, permissions, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers as users_serializers
from users import models as users_models
from .models import Subscription
from .services import create_checkout_session


class ProfileRetrieveAPIView(generics.RetrieveAPIView):
    """
    Получение профиля пользователя.

    **Метод**: GET
    **Параметры**:
    - `id`: Идентификатор пользователя.

    **Ответ**:
    - 200 OK: Данные профиля пользователя.
    - 404 Not Found: Если пользователь не найден.
    - 403 Forbidden: Если запрашивается профиль другого пользователя.
    """
    queryset = users_models.User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        user_id = self.kwargs.get("id")
        if self.request.user.id == user_id:
            return users_serializers.GetProfileSerializer
        else:
            return users_serializers.GetOrganizerProfileSerializer


class UserUpdateAPIView(generics.UpdateAPIView):
    """
    Обновление профиля пользователя.

    **Метод**: PUT
    **Тело запроса**:
    - Данные для обновления профиля.

    **Ответы**:
    - 200 OK: Профиль успешно обновлен.
    - 400 Bad Request: Ошибка валидации данных.
    - 403 Forbidden: Если пользователь пытается обновить чужой профиль.
    """
    queryset = users_models.User.objects.all()
    serializer_class = users_serializers.UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDestroyAPIView(generics.DestroyAPIView):
    """
    Удаление пользователя.

    **Метод**: DELETE
    **Параметры**:
    - `id`: Идентификатор пользователя.

    **Ответы**:
    - 204 No Content: Пользователь успешно удален.
    - 404 Not Found: Если пользователь не найден.
    - 403 Forbidden: Если пользователь пытается удалить чужой профиль.
    """
    queryset = users_models.User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    serializer_class = users_serializers.GetProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return users_models.User.objects.all()
        return users_models.User.objects.filter(id=user.id)


class SignInView(generics.GenericAPIView):
    """
    Вход пользователя.

    **Метод**: POST
    **Тело запроса**:
    - `username`: Имя пользователя.
    - `password`: Пароль.

    **Ответы**:
    - 200 OK: Успешный вход.
    - 400 Bad Request: Ошибка валидации данных.
    """
    serializer_class = users_serializers.SignInSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class SignUpAPIView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.

    **Метод**: POST
    **Тело запроса**:
    - `username`: Имя пользователя.
    - `email`: Электронная почта.
    - `password`: Пароль.

    **Ответы**:
    - 201 Created: Успешная регистрация, проверочный код отправлен на почту.
    - 400 Bad Request: Ошибка валидации данных.
    """
    serializer_class = users_serializers.SignUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {"detail": "Проверочный код отправлен на почту."}

        if settings.DEBUG:
            response_data.update(
                {
                    "debug_phone_number": user.phone_number,
                    "debug_code": user.checking_code,
                }
            )

        response_serializer = users_serializers.CodeResponseSerializer(
            data=response_data
        )
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AuthView(generics.GenericAPIView):
    """
    Аутентификация пользователя с проверочным кодом.

    **Метод**: POST
    **Тело запроса**:
    - `email`: Электронная почта пользователя.
    - `code`: Проверочный код.

    **Ответы**:
    - 200 OK: Успешная аутентификация.
    - 400 Bad Request: Ошибка валидации данных.
    """
    serializer_class = users_serializers.AuthCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            response_data = serializer.create(serializer.validated_data)
            return Response(response_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class CreateAPICheckoutSessionView(generics.GenericAPIView):
    """
    Создание сессии для оформления подписки.

    **Метод**: GET
    **Параметры**:
    - `email`: Электронная почта пользователя, на которого оформляется подписка.

    **Ответы**:
    - 200 OK: URL для оформления подписки.
    - 400 Bad Request: Ошибка, если email не указан или пользователь уже подписан.
    - 404 Not Found: Если пользователь не найден.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        # Проверяем, существует ли подписка
        if Subscription.objects.filter(
            user_id=request.user.id, subscribed_to__email=email
        ).exists():
            return JsonResponse(
                {"error": "Вы уже подписаны на этого пользователя."}, status=400
            )

        session = create_checkout_session(
            request.user, email, request
        )  # Передаем request

        if session is None:
            return JsonResponse({"error": "Пользователь не найден"}, status=404)

        return JsonResponse({"url": session.url})
