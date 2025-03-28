from django.urls import path

from .api_views import PostListAPIView, PostDetailAPIView, PostCreateAPIView
from .views import (
    PostCreateView,
    PostListView,
    PostDetailView,
    PostUpdateView,
    PostDeleteView,
    UserPostsView,
)

urlpatterns = [
    path("api/", PostListAPIView.as_view(), name="post-list"),
    path("api/<int:pk>/", PostDetailAPIView.as_view(), name="post-detail"),
    path("api/create/", PostCreateAPIView.as_view(), name="post-create"),
    # HTML URLs
    path("", PostListView.as_view(), name="home"),
    path("post/new/", PostCreateView.as_view(), name="post_create"),
    path("post/<int:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("my-posts/", UserPostsView.as_view(), name="user_posts"),
    path("post/edit/<int:pk>/", PostUpdateView.as_view(), name="post_edit"),
    path("post/delete/<int:pk>/", PostDeleteView.as_view(), name="post_delete"),
]
