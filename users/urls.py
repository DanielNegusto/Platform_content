from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    ProfileRetrieveAPIView,
    UserUpdateAPIView,
    UserDestroyAPIView,
    SignInView,
    SignUpAPIView,
    AuthView,
    CreateAPICheckoutSessionView,
)
from .views import (
    SignUpView,
    CustomLoginView,
    ProfileView,
    ConfirmationView,
    EditProfileView,
    CreateCheckoutSessionView,
    SuccessView,
    ErrorView,
    UserChatView,
    ModeratorChatView,
    ChatDetailView,
    CloseChatView,
    ModeratorPostView,
    ApprovePostView,
    RejectPostView,
)

urlpatterns = [
    path(
        "api/profile/<int:id>/",
        ProfileRetrieveAPIView.as_view(),
        name="profile-retrieve",
    ),
    path("api/profile/update/", UserUpdateAPIView.as_view(), name="profile-update"),
    path(
        "api/profile/delete/<int:id>/",
        UserDestroyAPIView.as_view(),
        name="profile-delete",
    ),
    path("api/signin/", SignInView.as_view(), name="signin"),
    path("api/signup/", SignUpAPIView.as_view(), name="signup"),
    path("api/auth/", AuthView.as_view(), name="auth"),  # Эндпоинт для получения токена
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "api/subscribe/<str:email>/",
        CreateAPICheckoutSessionView.as_view(),
        name="create_subscription_session",
    ),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/<str:email>/", ProfileView.as_view(), name="profile_detail"),
    path("confirmation/", ConfirmationView.as_view(), name="confirmation"),
    path("update/", EditProfileView.as_view(), name="edit_profile"),
    path(
        "create-subscription-session/<int:user_id>/",
        CreateCheckoutSessionView.as_view(),
        name="create_subscription_session",
    ),
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", ErrorView.as_view(), name="error"),
    path("user_chat/", UserChatView.as_view(), name="user_chat_view"),
    path(
        "moderator_chat/", ModeratorChatView.as_view(), name="moderator_chat_view"
    ),  # Чат модератора
    path("chat/<int:user_id>/", ChatDetailView.as_view(), name="chat_detail"),
    path("chat/close/<int:chat_id>/", CloseChatView.as_view(), name="close_chat"),
    path("moderator/posts/", ModeratorPostView.as_view(), name="moderator_post_view"),
    path(
        "moderator/posts/approve/<int:post_id>/",
        ApprovePostView.as_view(),
        name="approve_post",
    ),
    path(
        "moderator/posts/reject/<int:post_id>/",
        RejectPostView.as_view(),
        name="reject_post",
    ),
]
