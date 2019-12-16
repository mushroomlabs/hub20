from django.urls import path

from . import views

app_name = "hub20"


urlpatterns = [
    path("balances", views.TokenBalanceListView.as_view(), name="balance-list"),
    path("balance/<str:code>", views.TokenBalanceView.as_view(), name="balance-detail"),
    path("payment/orders", views.PaymentOrderListView.as_view(), name="payment-order-list"),
    path("payment/order/<int:pk>", views.PaymentOrderView.as_view(), name="payment-order-detail"),
    path("transfers", views.TransferListView.as_view(), name="transfer-list"),
    path("transfers/transfer/<int:pk>", views.TransferView.as_view(), name="transfer-detail"),
]
