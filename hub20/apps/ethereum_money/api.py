from django.urls import path

from . import views

app_name = "ethereum_money"


urlpatterns = [
    path("", views.TokenListView.as_view(), name="token-list"),
    path("token/<str:code>", views.TokenView.as_view(), name="token-detail"),
]
