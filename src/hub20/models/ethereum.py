from typing import TypeVar, Type, Any

from django.db import models
from gnosis.eth.django.models import EthereumAddressField, HexField
from model_utils.managers import QueryManager
from web3.auto import w3

from ..choices import ETHEREUM_NETWORKS


Wallet_T = TypeVar("Wallet_T", bound="Wallet")


class EthereumToken(models.Model):
    chain = models.PositiveIntegerField(
        choices=ETHEREUM_NETWORKS, default=ETHEREUM_NETWORKS.mainnet
    )
    ticker = models.CharField(max_length=5)
    name = models.CharField(max_length=60)
    decimals = models.PositiveIntegerField(default=18)
    address = EthereumAddressField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.ticker} ({self.get_chain_display()})"

    class Meta:
        unique_together = ("chain", "address")


class Wallet(models.Model):
    address = EthereumAddressField(unique=True, db_index=True)
    private_key = HexField(max_length=64, unique=True)
    is_locked = models.BooleanField(default=False)

    objects = models.Manager()
    unlocked = QueryManager(is_locked=False)
    locked = QueryManager(is_locked=True)

    def lock(self):
        self.is_locked = True
        self.save()

    def unlock(self):
        self.is_locked = False
        self.save()

    def __str__(self) -> str:
        return self.address

    @classmethod
    def generate(cls: Type[Wallet_T]) -> Wallet_T:
        account = w3.eth.account.create()
        return cls.objects.create(address=account.address, private_key=account.privateKey.hex())


class EthereumTokenAmountField(models.DecimalField):
    def __init__(self, *args: Any, **kw: Any) -> None:
        kw.setdefault("decimal_places", 18)
        kw.setdefault("max_digits", 32)

        super().__init__(*args, **kw)


class EthereumTokenValueModel(models.Model):
    amount = EthereumTokenAmountField()
    currency = models.ForeignKey(EthereumToken, on_delete=models.PROTECT)

    class Meta:
        abstract = True


__all__ = ["EthereumToken", "Wallet"]
