from django.urls import path

from . import views

app_name = "hub20"


urlpatterns = [
    path("payments", views.PaymentListView.as_view(), name="payment-list"),
    path("payments/payment/<int:pk>", views.PaymentView.as_view(), name="payment-detail",),
    path("tokens", views.TokenListView.as_view(), name="token-list"),
    path("tokens/token/<str:code>", views.TokenView.as_view(), name="token-detail"),
]
