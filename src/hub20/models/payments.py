from typing import Optional, Dict
import random

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from gnosis.eth.django.models import EthereumAddressField, HexField
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel, StatusModel

from blockchain.models import Transaction
from hub20.app_settings import PAYMENT_SETTINGS
from hub20.choices import PAYMENT_STATUS
from .ethereum import Wallet, EthereumTokenValueModel, EthereumToken
from .raiden import Raiden


def generate_raiden_payment_identifier():
    return random.randint(1, 2 ** 63 - 1)


class Payment(TimeStampedModel, EthereumTokenValueModel):
    EXPIRATION_TIME = PAYMENT_SETTINGS.payment_lifetime
    STATUS = PAYMENT_STATUS

    expiration_time = models.DateTimeField()
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    raiden = models.ForeignKey(Raiden, null=True, on_delete=models.PROTECT)
    raiden_payment_identifier = models.BigIntegerField(default=generate_raiden_payment_identifier)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    @property
    def chain_transfer_details(self) -> Dict:
        return {"address": self.wallet.address}

    @property
    def raiden_transfer_details(self) -> Dict:
        if not self.raiden:
            return {}

        return {
            "address": self.raiden.address,
            "identifier": self.raiden_payment_identifier,
        }

    @property
    def transfers(self):
        return self.transfer_set.filter(currency=self.currency).select_subclasses()

    @property
    def total_transferred(self):
        return self.transfers.aggregate(total=Sum("amount")).get("total") or 0

    @property
    def total_confirmed(self):
        return sum([transfer.amount for transfer in self.transfers if transfer.is_confirmed])

    @property
    def due_amount(self):
        return max(0, self.total_transferred - self.amount)

    @property
    def status(self):
        try:
            return self.logs.latest().status
        except PaymentLog.DoesNotExist:
            return None

    @property
    def is_finalized(self):
        return self.status not in [
            self.STATUS.requested,
            self.STATUS.partial,
            self.STATUS.received,
        ]

    def update_status(self):
        if self.is_finalized:
            return

        due_amount = self.due_amount
        total_transferred = self.total_transferred

        if total_transferred > 0 and due_amount > 0 and self.status != self.STATUS.partial:
            self.logs.create(status=self.STATUS.partial)
        elif total_transferred > 0 and due_amount == 0 and self.status != self.STATUS.received:
            self.logs.create(status=self.STATUS.received)
        elif self.total_transferred == 0 and self.status != self.STATUS.requested:
            self.logs.create(status=self.STATUS.requested)

    def maybe_finalize(self):
        if self.is_finalized:
            return

        should_expire = timezone.now() > self.expiration_time

        if self.total_confirmed >= self.amount:
            self.logs.create(status=self.STATUS.confirmed)
        elif should_expire:
            self.logs.create(status=self.STATUS.expired)

    @staticmethod
    def get_wallet() -> Wallet:
        unlocked_wallets = Wallet.unlocked.all()
        wallet = unlocked_wallets.order_by("?").first() or Wallet.generate()
        wallet.lock()

        return wallet

    @staticmethod
    def get_raiden(token: EthereumToken) -> Optional[Raiden]:
        return Raiden.objects.filter(token_networks__token=token).first()


class PaymentLog(TimeStampedModel, StatusModel):
    STATUS = PAYMENT_STATUS
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="logs")

    class Meta:
        get_latest_by = "created"
        unique_together = ("payment", "status")


class Transfer(TimeStampedModel, EthereumTokenValueModel):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    objects = InheritanceManager()

    def is_confirmed(self):
        return True


class InternalTransfer(Transfer):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class BlockchainTransfer(Transfer):
    address = EthereumAddressField(db_index=True)
    transaction_hash = HexField(max_length=64, db_index=True, unique=True)

    @property
    def transaction(self):
        tx = Transaction.objects.filter(hash=self.transaction_hash)
        return tx.select_related("block").first()

    @property
    def is_confirmed(self):
        if self.transaction is None:
            return False

        block = self.transaction and self.transaction.block
        return block.confirmations >= PAYMENT_SETTINGS.minimum_confirmations


class RaidenTransfer(Transfer):
    raiden = models.ForeignKey(Raiden, on_delete=models.PROTECT)


__all__ = ["Payment", "InternalTransfer", "BlockchainTransfer", "RaidenTransfer"]
