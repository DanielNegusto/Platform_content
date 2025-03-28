import secrets

import stripe
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
    code = "".join(secrets.choice("0123456789") for _ in range(4))
    print(code)
    return code


def get_user_by_phone(phone_number):
    user = users_models.User.objects.filter(phone_number=phone_number).first()
    return user


def create_checkout_session(current_user, target_user_email, request):
    try:
        target_user = users_models.User.objects.get(email=target_user_email)

        success_url = request.build_absolute_uri(
            f"/users/success/?subscribed_to_id={target_user.id}&user_id={current_user.id}"
        )
        cancel_url = request.build_absolute_uri("/users/cancel/")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "rub",
                        "product_data": {
                            "name": f"Подписка для {target_user.email}",
                        },
                        "unit_amount": 60000,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return session
    except users_models.User.DoesNotExist:
        return None
    except Exception as e:
        raise e
