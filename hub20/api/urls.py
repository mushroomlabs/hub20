from typing import Callable

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_auth.views import (
    LoginView,
    LogoutView,
    UserDetailsView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
)


def make_auth_view(url_path: str, view_class, view_name: str) -> Callable:
    return path(url_path, view_class.as_view(), name=view_name)


urlpatterns = [
    # URLs that do not require a session or valid token
    make_auth_view("api/accounts/password/reset", PasswordResetView, "rest_password_reset"),
    make_auth_view(
        "api/accounts/password/confirm", PasswordResetConfirmView, "rest_password_reset_confirm",
    ),
    make_auth_view("api/accounts/password/change", PasswordChangeView, "rest_password_change"),
    make_auth_view("api/accounts/user", UserDetailsView, "rest_user_details"),
    make_auth_view("api/session/login", LoginView, "rest_login"),
    make_auth_view("api/session/logout", LogoutView, "rest_logout"),
    path("api/register/", include("rest_auth.registration.urls")),
    path("api/tokens/", include("hub20.apps.ethereum_money.api", namespace="ethereum_money")),
    path("api/", include("hub20.apps.core.api", namespace="hub20")),
    path("admin/", admin.site.urls),
]

urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
