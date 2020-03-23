from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views
from .consumers import CheckoutConsumer, NotificationConsumer

app_name = "hub20"


router = SimpleRouter(trailing_slash=False)
router.register("payments", views.PaymentViewSet, basename="payments")
router.register("stores", views.StoreViewSet, basename="store")
router.register("checkout", views.CheckoutViewSet, basename="checkout")


urlpatterns = [
    path("balances", views.TokenBalanceListView.as_view(), name="balance-list"),
    path("balance/<str:code>", views.TokenBalanceView.as_view(), name="balance-detail"),
    path("payment/orders", views.PaymentOrderListView.as_view(), name="payment-order-list"),
    path("payment/order/<int:pk>", views.PaymentOrderView.as_view(), name="payment-order-detail"),
    path("transfers", views.TransferListView.as_view(), name="transfer-list"),
    path("transfers/transfer/<int:pk>", views.TransferView.as_view(), name="transfer-detail"),
] + router.urls


consumer_patterns = [
    path("checkout/<uuid:pk>", CheckoutConsumer),
    path("events", NotificationConsumer),
]
