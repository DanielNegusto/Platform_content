from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from .models import Post


class PostAPITests(APITestCase):

    def setUp(self):
        # Создание тестового пользователя
        self.user = User.objects.create_user(phone_number="123456789", password="test")
        self.free_post = Post.objects.create(
            title="Free Post",
            content="This is a free post.",
            status=Post.FREE,
            author=self.user,
        )
        self.premium_post = Post.objects.create(
            title="Premium Post",
            content="This is a premium post.",
            status=Post.PAID,
            author=self.user,
        )

    def test_post_list_authenticated(self):
        # Тестирование получения списка постов для авторизованного пользователя
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("post-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_post(self):
        # Тестирование получения конкретного поста
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("post-detail", args=[self.free_post.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Free Post")

    def test_create_post(self):
        # Тестирование создания нового поста
        self.client.force_authenticate(user=self.user)
        data = {"title": "New Post", "content": "This is a new post.", "status": "free"}
        response = self.client.post(reverse("post-create"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)  # Проверяем, что пост добавлен

    def test_update_post(self):
        # Тестирование обновления существующего поста
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Updated Post",
            "content": "This is an updated post.",
            "status": Post.FREE,
        }
        response = self.client.put(
            reverse("post-detail", args=[self.free_post.id]), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.free_post.refresh_from_db()  # Обновляем объект из базы данных
        self.assertEqual(
            self.free_post.title, "Updated Post"
        )  # Проверяем, что заголовок обновился

    def test_delete_post(self):
        # Тестирование удаления поста
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse("post-detail", args=[self.free_post.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 1)  # Проверяем, что пост удален

    def test_access_premium_post_unauthenticated(self):
        # Тестирование доступа к премиум посту для неавторизованного пользователя
        response = self.client.get(reverse("post-detail", args=[self.premium_post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_premium_post_authenticated(self):
        # Тестирование доступа к премиум посту для авторизованного пользователя
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("post-detail", args=[self.premium_post.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Premium Post")

    def test_get_post_create_view(self):
        # Проверяем, что GET-запрос возвращает правильный шаблон
        response = self.client.get(
            reverse("post_create")
        )  # Замените 'post_create' на ваш URL-нейм
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "post_form.html")

    def test_post_create_view_valid_form(self):
        data = {
            "title": "Test Post",
            "content": "This is a test post.",
            "categories": [],  # Укажите категории, если они необходимы
            "new_category": "New Category",  # Укажите новую категорию
        }
        response = self.client.post(reverse("post_create"), data)

        self.assertEqual(response.status_code, 200)

    def test_post_create_view_invalid_form(self):
        # Проверяем, что происходит с невалидной формой
        data = {
            "title": "",  # Пустое заглавие должно привести к ошибке
            "content": "This is a test post.",
            "categories": [],
            "new_category": "",
        }
        response = self.client.post(reverse("post_create"), data)
        self.assertEqual(response.status_code, 200)
