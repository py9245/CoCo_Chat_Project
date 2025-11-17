from django.urls import path

from accounts.views import (
    AvatarUploadView,
    DeleteAccountView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    ProfileUpdateView,
    ProfileView,
    RegisterView,
)


app_name = "accounts"

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("profile/update", ProfileUpdateView.as_view(), name="profile-update"),
    path("profile/password", PasswordChangeView.as_view(), name="password-change"),
    path("profile/avatar", AvatarUploadView.as_view(), name="avatar-upload"),
    path("profile/delete", DeleteAccountView.as_view(), name="account-delete"),
]
