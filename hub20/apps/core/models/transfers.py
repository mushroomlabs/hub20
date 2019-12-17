from typing import Optional
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel, StatusModel

from hub20.apps.blockchain.fields import EthereumAddressField, HexField
from hub20.apps.blockchain.models import Transaction
from hub20.apps.ethereum_money.models import EthereumTokenValueModel
from hub20.apps.raiden.models import Channel, Payment
from hub20.apps.core.choices import TRANSFER_EVENT_TYPES
from hub20.apps.core.signals import transfer_executed, transfer_failed, transfer_confirmed
from .accounting import UserAccount, Wallet, UserReserve

logger = logging.getLogger(__name__)


class TransferError(Exception):
    pass


class TransferOperationError(Exception):
    pass


class Transfer(TimeStampedModel, EthereumTokenValueModel):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers_sent"
    )
    memo = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=300, null=True, blank=True)
    objects = InheritanceManager()

    @property
    def status(self) -> Optional[str]:
        try:
            return self.events.latest().status
        except TransferEvent.DoesNotExist:
            return None

    @property
    def is_finalized(self) -> bool:
        return self.status in [
            TRANSFER_EVENT_TYPES.confirmed,
            TRANSFER_EVENT_TYPES.failed,
            TRANSFER_EVENT_TYPES.canceled,
        ]

    def _execute(self):
        pass

    def _make_reserve(self):
        pass

    def verify_conditions(self):

        transfer_amount = self.as_token_amount
        sender_account = UserAccount(self.sender)
        sender_balance = sender_account.get_balance(self.currency)

        if sender_balance < transfer_amount:
            raise TransferError("Insufficient balance")

    def execute(self):
        if self.is_finalized:
            logger.warning(f"{self} is already finalized as {self.status}")
            return

        try:
            self.verify_conditions()
            self._make_reserve()
            self._execute()
        except TransferError as exc:
            logger.info(f"{self} failed: {exc}")
            transfer_failed.send_robust(sender=Transfer, transfer=self, reason=str(exc))
        except Exception as exc:
            logger.exception(exc)


class InternalTransfer(Transfer):
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers_received"
    )

    @property
    def target(self):
        return self.receiver.username

    def clean(self):
        if self.sender == self.receiver:
            raise ValidationError("Sender and Receiver are the same")

    @transaction.atomic()
    def _execute(self):
        transfer_confirmed.send_robust(sender=InternalTransfer, transfer=self)


class ExternalTransfer(Transfer):
    recipient_address = EthereumAddressField(db_index=True)

    @property
    def target(self):
        return self.recipient_address

    @transaction.atomic()
    def _execute(self):
        transfer_amount = self.as_token_amount
        channel = Channel.select_for_transfer(self.recipient_address, transfer_amount)
        if channel:
            payment_id = channel.send(
                self.recipient_address, transfer_amount, payment_identifier=self.identifier
            )
            RaidenTransaction.objects.create(
                transfer=self, channel=channel, payment_identifier=payment_id
            )
        else:
            wallet = Wallet.select_for_transfer(transfer_amount)
            if wallet is None:
                raise TransferError("No channel nor wallet with funds to make transfer found")
            tx_hash = wallet.account.send(self.recipient_address, transfer_amount)
            BlockchainTransaction.objects.create(transfer=self, transaction_hash=tx_hash)
        transfer_executed.send_robust(sender=ExternalTransfer, transfer=self)

    @transaction.atomic()
    def _make_reserve(self):
        self.sender.balance_entries.create(amount=-self.amount, currency=self.currency)
        self.sender.reserves.update_or_create(
            usertransferreserve__transfer=self,
            defaults={"amount": self.amount, "currency": self.currency},
        )


class UserTransferReserve(UserReserve):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="reserve")


class BlockchainTransaction(TimeStampedModel):
    transfer = models.OneToOneField(
        Transfer, on_delete=models.CASCADE, related_name="chain_transaction"
    )
    transaction_hash = HexField(max_length=64, unique=True, db_index=True)

    @property
    def transaction(self) -> Optional[Transaction]:
        return Transaction.objects.filter(hash=self.transaction_hash).first()


class RaidenTransaction(TimeStampedModel):
    transfer = models.OneToOneField(
        Transfer, on_delete=models.CASCADE, related_name="raiden_transaction"
    )
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    identifier = models.PositiveIntegerField()

    @property
    def payment(self) -> Optional[Payment]:
        return self.channel.payments.filter(identifier=self.identifier).first()

    class Meta:
        unique_together = ("channel", "identifier")


class TransferEvent(TimeStampedModel, StatusModel):
    STATUS = TRANSFER_EVENT_TYPES

    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name="events")

    class Meta:
        get_latest_by = "created"
        unique_together = ("transfer", "status")


__all__ = [
    "Transfer",
    "InternalTransfer",
    "ExternalTransfer",
    "TransferError",
    "UserTransferReserve",
    "BlockchainTransaction",
    "RaidenTransaction",
]
