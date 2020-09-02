from rest_framework.routers import SimpleRouter

from . import views

app_name = "raiden"


router = SimpleRouter(trailing_slash=False)
router.register("nodes", views.RaidenViewSet, basename="raiden")
router.register("services/deposits", views.ServiceDepositViewSet, basename="deposit")


urlpatterns = router.urls
