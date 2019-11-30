from typing import Optional

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from gnosis.eth.django.models import EthereumAddressField, HexField
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel

from blockchain.models import Transaction
from .. import app_settings
from .accounts import Account
from .ethereum import Wallet, EthereumTokenValueModel, EthereumToken
from .raiden import Raiden


class Invoice(TimeStampedModel, EthereumTokenValueModel):
    EXPIRATION_TIME = app_settings.PAYMENTS.invoice_lifetime

    identifier = models.CharField(max_length=48, unique=True, db_index=True)
    expiration_time = models.DateTimeField()
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    raiden = models.ForeignKey(Raiden, null=True, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)

    @property
    def chain_payment_address(self) -> str:
        return self.wallet.address

    @property
    def raiden_payment_address(self) -> Optional[str]:
        return self.raiden and self.raiden.address

    @property
    def payments(self):
        return self.payment_set.filter(currency=self.currency).select_subclasses()

    @property
    def expired(self):
        return timezone.now() > self.expiration_time

    @property
    def paid(self):
        total_paid = self.payments.aggregate(total=Sum("amount")).get("total")
        return total_paid is not None and total_paid >= self.amount

    @staticmethod
    def get_wallet() -> Wallet:
        unlocked_wallets = Wallet.unlocked.all()
        wallet = unlocked_wallets.order_by("?").first() or Wallet.generate()
        wallet.lock()

        return wallet

    @staticmethod
    def get_raiden(token: EthereumToken) -> Optional[Raiden]:
        return Raiden.objects.filter(token_networks__token=token).first()


class Payment(TimeStampedModel, EthereumTokenValueModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT)
    objects = InheritanceManager()


class InternalPayment(Payment):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)


class BlockchainPayment(Payment):
    address = EthereumAddressField(db_index=True)
    transaction_hash = HexField(max_length=64, db_index=True, unique=True)

    @property
    def transaction(self):
        return Transaction.objects.filter(hash=self.transaction_hash).first()


class RaidenPayment(Payment):
    raiden = models.ForeignKey(Raiden, on_delete=models.PROTECT)
    identifier = models.PositiveIntegerField()


__all__ = ["Invoice", "InternalPayment", "BlockchainPayment", "RaidenPayment"]
