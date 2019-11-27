from typing import Optional
import datetime

from django.db import models
from gnosis.eth.django.models import EthereumAddressField, Sha3HashField
from model_utils import Choices
from model_utils.managers import QueryManager
from model_utils.models import StatusModel, TimeStampedModel


from .accounts import Account
from .ethereum import Wallet, EthereumTokenValueModel, EthereumToken
from .raiden import Raiden


INVOICE_LIFETIME = 15 * 60


class Invoice(StatusModel, TimeStampedModel, EthereumTokenValueModel):
    STATUS = Choices("requested", "ongoing", "completed", "canceled", "expired")

    identifier = models.CharField(max_length=48, unique=True, db_index=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    raiden = models.ForeignKey(Raiden, null=True, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)

    objects = models.Manager()
    closed = QueryManager(status__in=[STATUS.completed, STATUS.canceled, STATUS.expired])
    pending = QueryManager(status__in=[STATUS.requested, STATUS.ongoing])

    @property
    def expiration_time(self) -> datetime.datetime:
        return self.created + datetime.timedelta(seconds=INVOICE_LIFETIME)

    @property
    def chain_payment_address(self) -> str:
        return self.wallet.address

    @property
    def raiden_payment_address(self) -> Optional[str]:
        return self.raiden and self.raiden.address

    @staticmethod
    def get_wallet() -> Wallet:
        unlocked_wallets = Wallet.objects.exclude(
            invoice__status__in=[Invoice.STATUS.requested, Invoice.STATUS.ongoing]
        )
        wallet = unlocked_wallets.order_by("?").first()

        return wallet or Wallet.generate()

    @staticmethod
    def get_raiden(token: EthereumToken) -> Optional[Raiden]:
        return Raiden.objects.filter(token_networks__token=token).first()


class Payment(TimeStampedModel, EthereumTokenValueModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class InternalPayment(Payment):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)


class BlockchainPayment(Payment):
    address = EthereumAddressField(db_index=True)
    tx_hash = Sha3HashField()


class RaidenPayment(Payment):
    raiden = models.ForeignKey(Raiden, on_delete=models.PROTECT)
    identifier = models.PositiveIntegerField()


__all__ = ["Invoice", "InternalPayment", "BlockchainPayment", "RaidenPayment"]
