from typing import Optional

from django.shortcuts import get_object_or_404
from django.db.models.query import QuerySet
from rest_framework import generics
from rest_framework import permissions
from rest_framework.serializers import Serializer

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


class BaseInvoiceView(ReadWriteSerializerMixin):
    read_serializer_class = serializers.InvoiceReadSerializer
    write_serializer_class = serializers.InvoiceSerializer


class InvoiceListView(BaseInvoiceView, generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        return self.request.user.invoice_set.all()


class InvoiceView(BaseInvoiceView, generics.RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self) -> models.Invoice:
        return get_object_or_404(
            models.Invoice, pk=self.kwargs.get("pk"), account=self.request.user
        )


class TokenListView(generics.ListAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_queryset(self) -> QuerySet:
        return models.EthereumToken.objects.filter(address__isnull=False)


class TokenView(generics.RetrieveAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_object(self) -> models.EthereumToken:
        return get_object_or_404(models.EthereumToken, ticker=self.kwargs.get("code"))
