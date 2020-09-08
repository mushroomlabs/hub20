from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = "raiden"


router = SimpleRouter(trailing_slash=False)
router.register("channels", views.ChannelViewSet, basename="channel")


urlpatterns = [
    path("", views.RaidenView.as_view(), name="raiden-detail"),
    path("networks", views.TokenNetworkListView.as_view(), name="token-network-list"),
    path(
        "networks/<str:address>",
        views.TokenNetworkDetailView.as_view(),
        name="token-network-detail",
    ),
    path("services/deposits", views.ServiceDepositListView.as_view(), name="service-deposit-list"),
    path(
        "services/deposits/<int:pk>",
        views.ServiceDepositDetailView.as_view(),
        name="service-deposit-detail",
    ),
] + router.urls
