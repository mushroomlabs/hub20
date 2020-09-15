from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from eth_utils import is_address
from rest_framework import generics

from . import models, serializers


class TokenListView(generics.ListAPIView):
    serializer_class = serializers.HyperlinkedEthereumTokenSerializer

    def get_queryset(self) -> QuerySet:
        return models.EthereumToken.tracked.all()


class TokenView(generics.RetrieveAPIView):
    serializer_class = serializers.HyperlinkedEthereumTokenSerializer

    def get_object(self) -> models.EthereumToken:
        address = self.kwargs.get("address")

        if not is_address(address):
            raise Http404(f"{address} is not a valid token address")

        return get_object_or_404(models.EthereumToken, address=address)
