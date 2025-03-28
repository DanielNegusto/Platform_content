from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import FileExtensionValidator
from django.db import models
from core import constants

from users import services

NULLABLE = constants.NULLABLE


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="email", **NULLABLE)

    first_name = models.CharField(max_length=constants.CHAR_LENGTH, verbose_name="имя")

    last_name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="фамилия", **NULLABLE
    )

    avatar = models.ImageField(
        upload_to="users/avatars",
        verbose_name="аватарка",
        validators=[
            FileExtensionValidator(allowed_extensions=constants.IMAGE_EXTENSIONS),
            services.validata_avatar_size,
        ],
        **NULLABLE,
    )

    phone_number = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="номер телефона",
        unique=True,
    )
    description = models.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        **constants.NULLABLE,
        verbose_name="Описание",
    )

    checking_code = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="проверочный код", **NULLABLE
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="дата регистрации"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="дата изменения")

    is_active = models.BooleanField(default=False)

    # для супер пользователя
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    consent_personal_data = models.BooleanField(
        default=False, verbose_name="Согласие на обработку персональных данных"
    )
    password = models.CharField(max_length=constants.PASSWORD_CHAR_LENGTH, **NULLABLE)

    # Новое поле для отслеживания времени последней отправки кода
    last_code_sent = models.DateTimeField(
        **NULLABLE, verbose_name="время последней отправки кода"
    )

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def clean(self):
        super().clean()
        if self.email:
            self.email = str(self.email).lower()

    def __str__(self):
        return f"Пользователь {self.email}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscribers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("user", "subscribed_to")

    def __str__(self):
        return f"{self.user.email} подписан на {self.subscribed_to.email}"
