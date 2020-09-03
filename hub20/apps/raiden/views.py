from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from eth_utils import is_address
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Raiden, ServiceDeposit
from .serializers import DepositSerializer, RaidenSerializer, ServiceDepositTaskSerializer
from .tasks import send_service_deposit


class BaseRaidenAdminViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAdminUser,)


class RaidenViewSet(BaseRaidenAdminViewSet):
    queryset: QuerySet = Raiden.objects.all()

    serializer_class = RaidenSerializer
    lookup_field = "address"
    lookup_url_kwarg = "address"

    def get_object(self) -> Raiden:
        address = self.kwargs.get("address")
        if not is_address(address):
            raise Http404(f"{address} is not a valid raiden account address")

        return get_object_or_404(Raiden, address=address)


class ServiceDepositViewSet(BaseRaidenAdminViewSet):
    queryset: QuerySet = ServiceDeposit.objects.all()

    def get_serializer_class(self):
        return ServiceDepositTaskSerializer if self.action == "create" else DepositSerializer

    def create(self, request):
        serializer = ServiceDepositTaskSerializer(data=request.data)
        if serializer.is_valid():
            raiden = serializer.data["raiden"]
            amount = serializer.data["amount"]
            task = send_service_deposit.delay(raiden_id=raiden.id, token_amount=amount)
            return Response(dict(task_id=task.id), status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
