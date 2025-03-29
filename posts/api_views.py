from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .pagination import CustomPagination
from .serializers import PostSerializer


class PostListAPIView(generics.ListAPIView):
    """
    Получение списка постов.

    **Для авторизованных пользователей**: возвращает все посты.
    **Для неавторизованных пользователей**: возвращает только бесплатные посты.

    **Метод**: GET
    **Параметры**:
    - `status`: (необязательно) Фильтрует посты по статусу (например, "free" или "paid").

    **Ответ**:
    - 200 OK: Список постов.
    - 401 Unauthorized: Если пользователь не авторизован и пытается получить доступ к защищенным данным.
    """
    pagination_class = CustomPagination
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Post.objects.all()
        else:
            return Post.objects.filter(status=Post.FREE)


class PostCreateAPIView(generics.CreateAPIView):
    """
    Создание нового поста.

    Доступно только авторизованным пользователям.

    **Метод**: POST
    **Тело запроса**:
    - `title`: Заголовок поста.
    - `content`: Содержимое поста.
    - `status`: Статус поста ("free" или "paid").

    **Ответ**:
    - 201 Created: Пост успешно создан.
    - 400 Bad Request: Ошибка валидации данных.
    - 401 Unauthorized: Если пользователь не авторизован.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Получение, обновление или удаление поста.

    Доступно только авторизованным пользователям.

    **Методы**:
    - GET: Получить данные поста.
    - PUT: Обновить данные поста.
    - DELETE: Удалить пост.

    **Параметры**:
    - `id`: Идентификатор поста.

    **Ответы**:
    - 200 OK: Данные поста (для GET).
    - 204 No Content: Пост успешно обновлен или удален (для PUT и DELETE).
    - 404 Not Found: Пост не найден.
    - 401 Unauthorized: Если пользователь не авторизован.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)
