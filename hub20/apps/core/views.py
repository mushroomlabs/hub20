from typing import List, Optional

from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from hub20.apps.blockchain.app_settings import CHAIN_ID
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount

from . import models, serializers
from .permissions import IsAuthenticatedOrApiClient


class ReadWriteSerializerMixin(generics.GenericAPIView):
    """
    Overrides get_serializer_class to choose the read serializer
    for GET requests and the write serializer for POST requests.

    Set read_serializer_class and write_serializer_class attributes on a
    generic APIView
    """

    read_serializer_class: Optional[Serializer] = None
    write_serializer_class: Optional[Serializer] = None

    def get_serializer_class(self) -> Serializer:
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return self.get_write_serializer_class()
        return self.get_read_serializer_class()

    def get_read_serializer_class(self) -> Serializer:
        assert self.read_serializer_class is not None, (
            "'%s' should either include a `read_serializer_class` attribute,"
            "or override the `get_read_serializer_class()` method." % self.__class__.__name__
        )
        return self.read_serializer_class

    def get_write_serializer_class(self) -> Serializer:
        assert self.write_serializer_class is not None, (
            "'%s' should either include a `write_serializer_class` attribute,"
            "or override the `get_write_serializer_class()` method." % self.__class__.__name__
        )
        return self.write_serializer_class


class BasePaymentOrderView(ReadWriteSerializerMixin):
    read_serializer_class = serializers.PaymentOrderReadSerializer
    write_serializer_class = serializers.PaymentOrderSerializer


class PaymentOrderListView(BasePaymentOrderView, generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        return self.request.user.paymentorder_set.all()


class PaymentOrderView(BasePaymentOrderView, generics.RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self) -> models.PaymentOrder:
        return get_object_or_404(
            models.PaymentOrder, pk=self.kwargs.get("pk"), user=self.request.user
        )


class TransferListView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TransferSerializer

    def get_queryset(self) -> QuerySet:
        return self.request.user.transfers_sent.all()


class TransferView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TransferSerializer

    def get_object(self):
        try:
            return models.Transfer.objects.get_subclass(
                pk=self.kwargs.get("pk"), sender=self.request.user
            )
        except models.Transfer.DoesNotExist:
            raise Http404


class TokenBalanceListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TokenBalanceSerializer

    def get_queryset(self) -> List[EthereumTokenAmount]:
        return models.UserAccount(self.request.user).get_balances(chain_id=CHAIN_ID)


class TokenBalanceView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TokenBalanceSerializer

    def get_object(self) -> EthereumTokenAmount:
        user_account = models.UserAccount(self.request.user)
        token = get_object_or_404(EthereumToken, ticker=self.kwargs["code"], chain=CHAIN_ID)
        return user_account.get_balance(token)


class StoreListView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.StoreSerializer

    def get_queryset(self) -> QuerySet:
        return self.request.user.store_set.all()


class StoreView(generics.RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.StoreSerializer

    def get_object(self) -> models.Store:
        return self.request.user.store_set.filter(pk=self.kwargs["pk"]).first()


class CheckoutViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    permission_classes = (IsAuthenticatedOrApiClient,)
    serializer_class = serializers.HttpCheckoutSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return models.Checkout.objects.filter(
            store__in=models.Store.objects.accessible_to(self.request)
        )


class StoreViewSet(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.StoreSerializer

    def get_queryset(self) -> QuerySet:
        return self.request.user.store_set.all()
