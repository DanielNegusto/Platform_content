from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_code_email(email, code):
    subject = 'Ваш проверочный код'
    message = f'Ваш проверочный код: {code}'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
