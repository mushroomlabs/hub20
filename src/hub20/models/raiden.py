from django.db import models
from gnosis.eth.django.models import EthereumAddressField

from .ethereum import EthereumToken


class TokenNetwork(models.Model):
    address = EthereumAddressField()
    token = models.ForeignKey(EthereumToken, on_delete=models.CASCADE)


class Raiden(models.Model):
    url = models.URLField()
    address = EthereumAddressField()
    token_networks = models.ManyToManyField(TokenNetwork)


__all__ = ["TokenNetwork", "Raiden"]
