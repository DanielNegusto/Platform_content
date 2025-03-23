import secrets
from django.core.exceptions import ValidationError
from core.constants import MAX_AVATAR_SIZE
from . import models as users_models

"""Проверка размера файла"""


def validata_avatar_size(value):
    fielsize = value.size

    if fielsize > MAX_AVATAR_SIZE:
        raise ValidationError("Превышен допустимый размер файла")


"""Генкрация 4-х значного кода"""


def generate_code():
    code = ''.join(secrets.choice('0123456789') for _ in range(4))
    print(code)
    return code


def get_user_by_phone(phone_number):
    user = users_models.User.objects.filter(phone_number=phone_number).first()
    return user
