from __future__ import annotations

import logging
import random
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from model_utils.managers import InheritanceManager, QueryManager
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.fields import EthereumAddressField
from hub20.apps.blockchain.models import Transaction
from hub20.apps.core.choices import TRANSFER_EVENT_TYPES
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.client import EthereumClient
from hub20.apps.ethereum_money.models import EthereumTokenAmount, EthereumTokenValueModel
from hub20.apps.ethereum_money.typing import EthereumAccount_T
from hub20.apps.raiden.client.node import RaidenClient
from hub20.apps.raiden.exceptions import RaidenPaymentError
from hub20.apps.raiden.models import Channel, Raiden

from .accounting import UserAccount, UserReserve

logger = logging.getLogger(__name__)


EthereumAccount = get_ethereum_account_model()


class TransferError(Exception):
    pass


class TransferOperationError(Exception):
    pass


class BlockchainTransferExecutor(EthereumClient):
    def execute(self, transfer: ExternalTransfer):
        try:
            self.transfer(amount=transfer.as_token_amount, address=transfer.recipient_address)
        except Exception as exc:
            raise TransferError(str(exc)) from exc

    @classmethod
    def can_reach(cls, transfer: ExternalTransfer) -> bool:
        return True

    @classmethod
    def select_account(
        cls, transfer: ExternalTransfer, transfer_fee: EthereumTokenAmount
    ) -> Optional[EthereumAccount_T]:
        assert transfer_fee.is_ETH

        ETH = transfer_fee.currency

        token_required = transfer.as_token_amount
        accounts = EthereumAccount.objects.all()

        if token_required.is_ETH:
            token_required += transfer_fee
            funded_accounts = [
                account for account in accounts if account.get_balance(ETH) >= token_required
            ]
        else:
            funded_accounts = [
                account
                for account in accounts
                if account.get_balance(token_required.currency) >= token_required
                and account.get_balance(ETH) >= transfer_fee
            ]

        try:
            return random.choice(funded_accounts)
        except IndexError:
            return None

    @classmethod
    def make_for_transfer(cls, transfer: ExternalTransfer):
        transfer_fee = cls.estimate_transfer_fees()
        account = cls.select_account(transfer=transfer, transfer_fee=transfer_fee)

        return account and cls(account=account)


class RaidenTransferExecutor(RaidenClient):
    def execute(self, transfer: ExternalTransfer):
        try:
            self.transfer(
                amount=transfer.as_token_amount,
                address=transfer.recipient_address,
                identifier=self._ensure_valid_identifier(transfer.identifier),
            )
        except RaidenPaymentError as exc:
            raise TransferError(exc.message) from exc

        TransferExecution.objects.create(transfer=transfer)
        TransferConfirmation.objects.create(transfer=transfer)

    @classmethod
    def can_reach(cls, transfer: ExternalTransfer) -> bool:
        return Channel.available.filter(token_network__token=transfer.currency).exists()

    @classmethod
    def select_account(cls, transfer: ExternalTransfer) -> Optional[EthereumAccount_T]:
        return Raiden.get() if cls.can_reach(transfer) else None

    @classmethod
    def make_for_transfer(cls, transfer: ExternalTransfer):
        if not settings.HUB20_RAIDEN_ENABLED:
            return None

        if not cls.can_reach(transfer):
            return None

        raiden = cls.select_account(transfer)
        return raiden and cls(raiden)


class Transfer(TimeStampedModel, EthereumTokenValueModel):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers_sent"
    )
    memo = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=300, null=True, blank=True)
    objects = InheritanceManager()

    @property
    def status(self) -> str:
        if self.failed:
            return TRANSFER_EVENT_TYPES.failed
        elif self.canceled:
            return TRANSFER_EVENT_TYPES.canceled
        elif self.confirmed:
            return TRANSFER_EVENT_TYPES.confirmed
        elif self.executed:
            return TRANSFER_EVENT_TYPES.executed
        else:
            return TRANSFER_EVENT_TYPES.scheduled

    @property
    def canceled(self):
        return TransferCancellation.objects.filter(transfer=self).exists()

    @property
    def confirmed(self):
        return TransferConfirmation.objects.filter(transfer=self).exists()

    @property
    def executed(self):
        return TransferExecution.objects.filter(transfer=self).exists()

    @property
    def failed(self):
        return TransferFailure.objects.filter(transfer=self).exists()

    @property
    def is_finalized(self) -> bool:
        return self.status != TRANSFER_EVENT_TYPES.scheduled

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
            TransferFailure.objects.create(transfer=self)
        except Exception as exc:
            TransferFailure.objects.create(transfer=self)
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
        try:
            self.receiver.balance_entries.create(amount=self.amount, currency=self.currency)
            self.sender.balance_entries.create(amount=-self.amount, currency=self.currency)
            TransferExecution.objects.create(transfer=self)
            TransferConfirmation.objects.create(transfer=self)
        except Exception as exc:
            raise TransferError from exc


class ExternalTransfer(Transfer):
    EXECUTORS = (RaidenTransferExecutor, BlockchainTransferExecutor)
    recipient_address = EthereumAddressField(db_index=True)
    objects = models.Manager()
    unconfirmed = QueryManager(confirmation__isnull=True)

    @property
    def target(self):
        return self.recipient_address

    @transaction.atomic()
    def _execute(self):
        try:
            executor_class = next(e for e in self.EXECUTORS if e.make_for_transfer(self))
            executor = executor_class.make_for_transfer(self)
            executor.execute(self)
        except StopIteration:
            raise TransferError("No executor found to complete transfer")

    @transaction.atomic()
    def _make_reserve(self):
        self.sender.balance_entries.create(amount=-self.amount, currency=self.currency)
        self.sender.reserves.update_or_create(
            usertransferreserve__transfer=self,
            defaults={"amount": self.amount, "currency": self.currency},
        )


class UserTransferReserve(UserReserve):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="reserve")


class TransferExecution(TimeStampedModel):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="execution")


class BlockchainTransferExecution(TransferExecution):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)


class TransferConfirmation(TimeStampedModel):
    transfer = models.OneToOneField(
        Transfer, on_delete=models.CASCADE, related_name="confirmation"
    )


class TransferFailure(TimeStampedModel):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="failure")


class TransferCancellation(TimeStampedModel):
    transfer = models.OneToOneField(
        Transfer, on_delete=models.CASCADE, related_name="cancellation"
    )
    canceled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


__all__ = [
    "BlockchainTransferExecutor",
    "Transfer",
    "TransferFailure",
    "TransferCancellation",
    "TransferExecution",
    "BlockchainTransferExecution",
    "TransferConfirmation",
    "InternalTransfer",
    "ExternalTransfer",
    "TransferError",
    "UserTransferReserve",
]
