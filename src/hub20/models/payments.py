from typing import Optional
import datetime

from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from gnosis.eth.django.models import EthereumAddressField
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel

from blockchain.models import Transaction

from .accounts import Account
from .ethereum import Wallet, EthereumTokenValueModel, EthereumToken
from .raiden import Raiden


class Invoice(TimeStampedModel, EthereumTokenValueModel):
    EXPIRATION_TIME = 15 * 60

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
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)


class RaidenPayment(Payment):
    raiden = models.ForeignKey(Raiden, on_delete=models.PROTECT)
    identifier = models.PositiveIntegerField()


@receiver(pre_save, sender=Invoice)
def on_invoice_created(sender, **kw):
    instance = kw["instance"]
    created_time = instance.created or timezone.now()
    if instance.expiration_time is None:
        instance.expiration_time = created_time + datetime.timedelta(
            seconds=Invoice.EXPIRATION_TIME
        )


__all__ = ["Invoice", "InternalPayment", "BlockchainPayment", "RaidenPayment"]
