import stripe
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework import generics, permissions, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, Token

from . import serializers as users_serializers, services
from users import models as users_models
from .models import User


class ProfileRetrieveAPIView(generics.RetrieveAPIView):
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
    queryset = users_models.User.objects.all()
    serializer_class = users_serializers.UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDestroyAPIView(generics.DestroyAPIView):
    queryset = users_models.User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    serializer_class = users_serializers.GetProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return users_models.User.objects.all()
        return users_models.User.objects.filter(id=user.id)


class SignInView(generics.GenericAPIView):
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
    serializer_class = users_serializers.SignUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {"detail": "Проверочный код отправлен на почту."}

        if settings.DEBUG:
            response_data.update({
                "debug_phone_number": user.phone_number,
                "debug_code": user.checking_code
            })

        response_serializer = users_serializers.CodeResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AuthView(generics.GenericAPIView):
    serializer_class = users_serializers.AuthCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Проверка валидности данных

        # Вызов метода create из сериализатора для обработки логики аутентификации
        try:
            response_data = serializer.create(serializer.validated_data)
            return Response(response_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class CreateAPICheckoutSessionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)

        try:
            user = request.user  # Используем аутентифицированного пользователя

            # Создайте сессию платежа для подписки
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'rub',
                            'product_data': {
                                'name': f'Подписка для {user.email}',
                            },
                            'unit_amount': 60000,  # 600 рублей = 60000 копеек
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri(f'/users/success/?subscribed_to_id={user.id}&user_id={user.id}'),
                cancel_url=request.build_absolute_uri('/users/cancel/'),
            )

            return JsonResponse({'url': session.url})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)