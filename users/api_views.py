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
    lookup_field = "id"
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
