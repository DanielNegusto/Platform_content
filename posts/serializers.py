from rest_framework import serializers

from users.models import Subscription
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "status",
            "author_email",
            "image",
            "video",
            "categories",
        ]
        read_only_fields = ["author"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context["request"].user

        # Проверяем, является ли текущий пользователь автором поста
        is_author = user == instance.author

        # Проверяем, есть ли у пользователя подписка на автора
        is_subscribed = Subscription.objects.filter(
            user=user, subscribed_to=instance.author
        ).exists()

        if instance.status == Post.PAID:
            if is_author or is_subscribed:
                # Если пользователь автор поста или подписан, возвращаем полное представление
                return representation
            else:
                # Если платный пост, возвращаем ограниченные поля для неподписанных пользователей
                limited_representation = {
                    "id": instance.id,
                    "title": representation["title"],
                    "status": representation["status"],
                    "author_email": representation["author_email"],
                }
                return limited_representation

        # Для бесплатных постов возвращаем все поля
        return representation
