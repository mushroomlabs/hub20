from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter(trailing_slash=False)
router.register("channels", views.ChannelViewSet, basename="channel")
router.register("networks", views.TokenNetworkViewSet, basename="token-network")

urlpatterns = [
    path("", views.RaidenView.as_view(), name="raiden-detail"),
    path("services/deposits", views.ServiceDepositListView.as_view(), name="service-deposit-list"),
    path(
        "services/deposits/<int:pk>",
        views.ServiceDepositDetailView.as_view(),
        name="service-deposit-detail",
    ),
] + router.urls
