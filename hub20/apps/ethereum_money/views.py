from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics


from hub20.apps.blockchain.app_settings import CHAIN_ID
from . import models
from . import serializers


class TokenListView(generics.ListAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_queryset(self) -> QuerySet:
        return models.EthereumToken.objects.filter(chain=CHAIN_ID, address__isnull=False)


class TokenView(generics.RetrieveAPIView):
    serializer_class = serializers.EthereumTokenSerializer

    def get_object(self) -> models.EthereumToken:
        return get_object_or_404(
            models.EthereumToken, chain=CHAIN_ID, ticker=self.kwargs.get("code")
        )
