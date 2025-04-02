from unittest.mock import patch

from django.test import TestCase

from .models import Subscription, User
from django.urls import reverse

from .serializers import SignInSerializer


class UserModelTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            phone_number="1234567890", password="password123", email="user1@example.com"
        )
        self.user2 = User.objects.create_user(
            phone_number="0987654321", password="password456", email="user2@example.com"
        )

    def test_user_creation(self):
        self.assertEqual(self.user1.phone_number, "1234567890")
        self.assertEqual(self.user1.email, "user1@example.com")
        self.assertTrue(self.user1.check_password("password123"))

    def test_user_str(self):
        self.assertEqual(str(self.user1), "Пользователь user1@example.com")

    def test_user_email_lowercase(self):
        user = User.objects.create_user(
            phone_number="1111111111", password="password789", email="test@example.com"
        )
        self.assertEqual(user.email, "test@example.com")

    def test_user_subscription(self):
        subscription = Subscription.objects.create(
            user=self.user1, subscribed_to=self.user2
        )
        self.assertEqual(subscription.user, self.user1)
        self.assertEqual(subscription.subscribed_to, self.user2)

    def test_unique_subscription(self):
        Subscription.objects.create(user=self.user1, subscribed_to=self.user2)
        with self.assertRaises(Exception):
            Subscription.objects.create(user=self.user1, subscribed_to=self.user2)

    def test_subscription_str(self):
        subscription = Subscription.objects.create(
            user=self.user1, subscribed_to=self.user2
        )
        self.assertEqual(
            str(subscription), "user1@example.com подписан на user2@example.com"
        )

    def test_user_can_have_multiple_subscriptions(self):
        user3 = User.objects.create_user(
            phone_number="2222222222", password="password000", email="user3@example.com"
        )
        Subscription.objects.create(user=self.user1, subscribed_to=self.user2)
        Subscription.objects.create(user=self.user1, subscribed_to=user3)

        self.assertEqual(self.user1.subscriptions.count(), 2)


class UserViewsTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            phone_number="1234567890", password="password123", email="user1@example.com"
        )
        self.user2 = User.objects.create_user(
            phone_number="0987654321", password="password456", email="user2@example.com"
        )

    def test_signup_view(self):
        response = self.client.post(
            reverse("signup"),
            {
                "phone_number": "1111111111",
                "password": "password789",
                "email": "user3@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.post(
            reverse("login"), {"phone_number": "1234567890", "password": "password123"}
        )
        self.assertEqual(response.status_code, 200)

        # Проверка неверного входа
        response = self.client.post(
            reverse("login"),
            {"phone_number": "1234567890", "password": "wrongpassword"},
        )
        self.assertEqual(
            response.status_code, 200
        )  # Проверка, что остались на странице входа
        self.assertContains(response, "Неверный номер телефона или пароль.")

    def test_profile_view(self):
        self.client.login(
            phone_number="1234567890", password="password123"
        )  # Вход в систему
        response = self.client.get(reverse("profile"))  # Запрос к профилю
        self.assertEqual(
            response.status_code, 302
        )  # Проверка успешного доступа к профилю

    def test_create_checkout_session_view(self):
        self.client.login(
            phone_number="1234567890", password="password123"
        )  # Вход в систему
        response = self.client.post(
            reverse("create_subscription_session", args=[self.user2.id])
        )  # Создание сессии
        self.assertEqual(response.status_code, 200)


class SignInSerializerTest(TestCase):
    def setUp(self):
        self.phone_number = "123456789"
        self.user = User.objects.create_user(
            phone_number=self.phone_number,
            # Добавьте другие необходимые поля, если они есть
        )

    @patch("users.services.get_user_by_phone")  # Замените на правильный путь
    @patch("users.services.generate_code")  # Замените на правильный путь
    @patch("users.tasks.send_code_email.delay")  # Замените на правильный путь
    def test_validate_success(
        self, mock_send_code_email, mock_generate_code, mock_get_user_by_phone
    ):
        mock_get_user_by_phone.return_value = self.user
        mock_generate_code.return_value = "123456"

        serializer = SignInSerializer(data={"phone_number": self.phone_number})
        self.assertTrue(serializer.is_valid())
        response = serializer.validated_data

        self.assertEqual(
            response["detail"], "Проверочный код отправлен на указанный номер телефона."
        )
        self.assertEqual(self.user.checking_code, "123456")
        self.assertIsNotNone(self.user.last_code_sent)
        mock_send_code_email.assert_called_once_with(self.phone_number, "123456")

    @patch("users.services.get_user_by_phone")  # Замените на правильный путь
    def test_validate_user_not_found(self, mock_get_user_by_phone):
        mock_get_user_by_phone.return_value = None

        serializer = SignInSerializer(data={"phone_number": self.phone_number})
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertEqual(serializer.errors["detail"], ["Пользователь не найден."])
