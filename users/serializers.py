from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils import timezone

from users import models as users_models
from users import services as users_services
from core import constants
from . import tasks as mailing_tasks


class GetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.User
        fields = (
            "id",
            "avatar",
            "first_name",
            "email",
            "phone_number",
            "description",
            "consent_personal_data",
        )


class GetOrganizerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.User
        fields = (
            "id",
            "avatar",
            "first_name",
            "description",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.User
        fields = (
            "id",
            "avatar",
            "first_name",
            "email",
            "phone_number",
            "description",
            "consent_personal_data",
        )

    def update(self, instance, validated_data):
        new_phone_number = validated_data.get("phone_number", instance.phone_number)

        if instance.phone_number != new_phone_number:
            checking_code = users_services.generate_code()
            validated_data["checking_code"] = checking_code
            validated_data["is_active"] = False
            mailing_tasks.send_code_sms.delay(new_phone_number, checking_code)

        return super().update(instance, validated_data)


class PhoneNumberOnlyTokenObtainSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        user = users_services.get_user_by_phone(phone_number)

        if not user:
            raise serializers.ValidationError({"phone_number": "Пользователь не найден."})

        if not user.is_active:
            raise serializers.ValidationError({"phone_number": "Пользователь не подтверждён."})

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class CodeResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    debug_phone_number = serializers.CharField(required=False)
    debug_code = serializers.CharField(required=False)


class UserInfoMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    phone_number = serializers.CharField()
    first_name = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserInfoMiniSerializer()


class SignInSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        user = users_services.get_user_by_phone(phone_number)

        if not user:
            raise serializers.ValidationError({"detail": "Пользователь не найден."})

        last_code_time = getattr(user, 'last_code_sent', None)

        if last_code_time:
            diff = constants.CODE_SEND_FREQUENCY - (timezone.now() - last_code_time)
            remaining_seconds = diff.total_seconds()

            if remaining_seconds > 0:
                minutes, seconds = divmod(int(remaining_seconds), 60)
                message = "Слишком часто отправляем проверочный код. Попробуйте через"

                if minutes > 0:
                    message += f" {minutes} мин." + (f" {seconds} сек." if seconds > 0 else "")
                else:
                    message += f" {seconds} сек."

                raise serializers.ValidationError({"detail": message})

        checking_code = users_services.generate_code()
        user.checking_code = checking_code
        user.last_code_sent = timezone.now()
        user.save(update_fields=["checking_code", "last_code_sent"])

        mailing_tasks.send_code_email.delay(phone_number, checking_code)

        response = {"detail": "Проверочный код отправлен на указанный номер телефона."}

        if settings.DEBUG:
            response.update({
                "debug_phone_number": phone_number,
                "debug_code": checking_code
            })

        return response


class SignUpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    consent_personal_data = serializers.BooleanField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        email = attrs.get("email")
        consent = attrs.get("consent_personal_data")

        if not consent:
            raise serializers.ValidationError(
                {"consent_personal_data": "Необходимо согласие на обработку персональных данных."})

        if users_models.User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "Пользователь с таким номером телефона уже существует."})

        if users_models.User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Пользователь с такой электронной почтой уже существует."})

        return attrs

    def create(self, validated_data):
        # Хэшируем пароль
        hashed_password = make_password(validated_data["password"])

        # Генерация проверочного кода
        checking_code = users_services.generate_code()

        user = users_models.User.objects.create(
            phone_number=validated_data["phone_number"],
            email=validated_data["email"],
            password=hashed_password,  # Сохраняем хэшированный пароль
            consent_personal_data=validated_data["consent_personal_data"],
            checking_code=checking_code,
            last_code_sent=timezone.now()
        )

        # Отправка кода на электронную почту
        mailing_tasks.send_code_email.delay(user.email, checking_code)

        return user


class AuthCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    checking_code = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        checking_code = attrs.get("checking_code")

        user = users_services.get_user_by_phone(phone_number)
        if not user:
            raise serializers.ValidationError({"phone_number": "Пользователь не найден."})

        if user.checking_code != checking_code:
            raise serializers.ValidationError({"checking_code": "Неверный проверочный код."})

        return attrs  # Возвращаем атрибуты для дальнейшей обработки

    def create(self, validated_data):
        phone_number = validated_data["phone_number"]
        user = users_services.get_user_by_phone(phone_number)

        # Обновляем состояние пользователя
        user.is_active = True
        user.checking_code = None
        user.save(update_fields=["is_active", "checking_code"])

        refresh = RefreshToken.for_user(user)

        user_info = {
            "id": user.id,
            "phone_number": user.phone_number,
            "email": user.email,
        }

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user_info
        }
