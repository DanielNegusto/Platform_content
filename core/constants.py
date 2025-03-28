# настройка send_mail
from datetime import timedelta

from decouple import config

DEBUG = config("DEBUG", "False") == "True"

EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = config("EMAIL_USE_TLS")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

# не обязательные поля для моделей
NULLABLE = {"blank": True, "null": True}

CHAR_LENGTH = 50
PASSWORD_CHAR_LENGTH = 130

DESCRIPTION_LENGTH = 2000

IMAGE_EXTENSIONS = ("jpg", "jpeg", "png")

MAX_AVATAR_SIZE = 10 * 1024 * 1024

CODE_SEND_FREQUENCY = timedelta(days=0, hours=0, minutes=0, seconds=50)

# Переменные Celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND")

POSTGRES_DB = config("POSTGRES_DB", "django")
POSTGRES_USER = config("POSTGRES_USER", "django")
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", "")
DB_HOST = config("DB_HOST", "")
DB_PORT = config("DB_PORT", 5432)

STRIPE_TEST_PUBLIC_KEY = config("STRIPE_TEST_PUBLIC_KEY")
STRIPE_TEST_SECRET_KEY = config("STRIPE_TEST_SECRET_KEY")
