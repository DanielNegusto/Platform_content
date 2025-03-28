from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .pagination import CustomPagination
from .serializers import PostSerializer


class PostListAPIView(generics.ListAPIView):
    pagination_class = CustomPagination
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            # Возвращаем все посты для авторизованных пользователей
            return Post.objects.all()
        else:
            # Для неавторизованных пользователей возвращаем только бесплатные посты
            return Post.objects.filter(status=Post.FREE)


class PostCreateAPIView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)
