from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = "Создает суперпользователя с заданными данными"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        email = "admin@example.com"
        phone = "12345678910"
        password = "admin"

        # Проверяем, существует ли пользователь с таким email
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING("Суперпользователь уже создан."))
        else:
            user = User.objects.create_superuser(
                phone_number=phone, email=email, password=password
            )
            user.save()
            self.stdout.write(self.style.SUCCESS("Суперпользователь успешно создан."))
