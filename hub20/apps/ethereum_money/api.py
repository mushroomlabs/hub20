from django.urls import path

from . import views

app_name = "ethereum_money"


urlpatterns = [
    path("", views.TokenListView.as_view(), name="token-list"),
    path("token/<str:code>", views.TokenView.as_view(), name="token-detail"),
    path(
        "rates/<str:token>/<str:currency>",
        views.ExchangeRateView.as_view(),
        name="exchange-rate-detail",
    ),
]
