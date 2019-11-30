from typing import TypeVar, Type, Any, Optional

from django.db import models
from ethtoken.abi import EIP20_ABI
from gnosis.eth.django.models import EthereumAddressField, HexField
from model_utils.models import TimeStampedModel
from model_utils.managers import QueryManager
from web3.contract import Contract

from blockchain.models import make_web3, CURRENT_CHAIN_ID
from blockchain.choices import ETHEREUM_CHAINS


Wallet_T = TypeVar("Wallet_T", bound="Wallet")


class EthereumToken(models.Model):
    chain = models.PositiveIntegerField(choices=ETHEREUM_CHAINS, default=CURRENT_CHAIN_ID)
    ticker = models.CharField(max_length=5)
    name = models.CharField(max_length=60)
    decimals = models.PositiveIntegerField(default=18)
    address = EthereumAddressField(null=True, blank=True)

    objects = models.Manager()
    ERC20tokens = QueryManager(address__isnull=False)
    ethereum = QueryManager(address__isnull=True)

    def __str__(self) -> str:
        return f"{self.ticker} ({self.get_chain_display()})"

    def get_contract(self) -> Optional[Contract]:
        if not self.address:
            return

        w3 = make_web3()
        return w3.eth.contract(address=self.address, abi=EIP20_ABI)

    @staticmethod
    def ETH(chain_id):
        eth, _ = EthereumToken.objects.get_or_create(
            chain=chain_id, ticker="ETH", defaults={"name": "Ethereum"}
        )
        return eth

    class Meta:
        unique_together = ("chain", "address")


class Wallet(TimeStampedModel):
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
        w3 = make_web3()
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
