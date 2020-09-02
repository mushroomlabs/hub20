from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from eth_utils import is_address
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from . import serializers
from .models import Raiden, ServiceDeposit


class BaseRaidenAdminViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAdminUser,)


class RaidenViewSet(BaseRaidenAdminViewSet):
    queryset: QuerySet = Raiden.objects.all()

    serializer_class = serializers.RaidenSerializer
    lookup_field = "address"
    lookup_url_kwarg = "address"

    def get_object(self) -> Raiden:
        address = self.kwargs.get("address")
        if not is_address(address):
            raise Http404(f"{address} is not a valid raiden account address")

        return get_object_or_404(Raiden, address=address)


class ServiceDepositViewSet(mixins.CreateModelMixin, BaseRaidenAdminViewSet):
    queryset: QuerySet = ServiceDeposit.objects.all()
    serializer_class = serializers.DepositSerializer
