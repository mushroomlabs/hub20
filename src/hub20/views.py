from typing import Optional, List

from django.shortcuts import get_object_or_404
from django.db.models.query import QuerySet
from rest_framework import generics
from rest_framework import permissions
from rest_framework.serializers import Serializer

from blockchain.models import CURRENT_CHAIN_ID
from . import models
from . import serializers


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


class BasePaymentView(ReadWriteSerializerMixin):
    read_serializer_class = serializers.PaymentReadSerializer
    write_serializer_class = serializers.PaymentSerializer


class PaymentListView(BasePaymentView, generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        return self.request.user.payment_set.all()


class PaymentView(BasePaymentView, generics.RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self) -> models.Payment:
        return get_object_or_404(models.Payment, pk=self.kwargs.get("pk"), user=self.request.user)


class TokenBalanceListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TokenBalanceSerializer

    def get_queryset(self) -> List[models.EthereumTokenAmount]:
        return models.UserAccount(self.request.user).get_balances()


class TokenBalanceView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.TokenBalanceSerializer

    def get_object(self) -> models.EthereumTokenAmount:
        user_account = models.UserAccount(self.request.user)
        token = get_object_or_404(
            models.EthereumToken, ticker=self.kwargs["code"], chain=CURRENT_CHAIN_ID
        )
        return user_account.get_balance(token)


class TokenListView(generics.ListAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_queryset(self) -> QuerySet:
        return models.EthereumToken.objects.filter(address__isnull=False)


class TokenView(generics.RetrieveAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_object(self) -> models.EthereumToken:
        return get_object_or_404(models.EthereumToken, ticker=self.kwargs.get("code"))
