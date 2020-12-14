from __future__ import annotations

import logging
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from model_utils.managers import QueryManager
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.fields import EthereumAddressField
from hub20.apps.blockchain.models import Transaction
from hub20.apps.blockchain.typing import Address
from hub20.apps.core.choices import PAYMENT_NETWORKS, TRANSFER_STATUS
from hub20.apps.ethereum_money.client import EthereumClient
from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenValueModel,
)
from hub20.apps.raiden.client.node import RaidenClient
from hub20.apps.raiden.exceptions import RaidenPaymentError
from hub20.apps.raiden.models import Payment

logger = logging.getLogger(__name__)
User = get_user_model()


class TransferError(Exception):
    pass


class TransferOperationError(Exception):
    pass


class BlockchainTransferExecutor(EthereumClient):
    def execute(self, transfer: Transfer):
        try:
            tx_hash = self.transfer(amount=transfer.as_token_amount, address=transfer.address)
            TransferReceipt.objects.create(
                transfer=transfer, network=PAYMENT_NETWORKS.blockchain, identifier=tx_hash.hex()
            )
        except Exception as exc:
            raise TransferError(str(exc)) from exc


class RaidenTransferExecutor(RaidenClient):
    def execute(self, transfer: Transfer):
        try:
            payment_identifier = self.transfer(
                amount=transfer.as_token_amount,
                address=transfer.address,
                identifier=self._ensure_valid_identifier(transfer.identifier),
            )
        except RaidenPaymentError as exc:
            raise TransferError(exc.message) from exc

        TransferReceipt.objects.create(
            transfer=transfer, network=PAYMENT_NETWORKS.raiden, identifier=payment_identifier
        )


class InternalTransferExecutor:
    def execute(self, transfer: Transfer):
        TransferReceipt.objects.create(
            transfer=transfer, network=PAYMENT_NETWORKS.internal, identifier=transfer.identifier
        )
        TransferExecution.objects.create(transfer=transfer)

    @classmethod
    def select_for_transfer(cls, amount: EthereumTokenAmount, target: Optional[User]):
        if target:
            return cls()


class Transfer(TimeStampedModel, EthereumTokenValueModel):
    EXECUTORS = (InternalTransferExecutor, RaidenTransferExecutor, BlockchainTransferExecutor)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers_sent"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transfers_received",
        null=True,
    )
    address = EthereumAddressField(db_index=True, null=True)
    memo = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=300, null=True, blank=True)
    execute_on = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    processed = QueryManager(receipt__isnull=False)
    canceled = QueryManager(cancellation__isnull=False)
    failed = QueryManager(failure__isnull=False)
    executed = QueryManager(execution__isnull=False)
    pending = QueryManager(
        receipt__isnull=True,
        cancellation__isnull=True,
        failure__isnull=True,
        execution__isnull=True,
    )

    @property
    def status(self) -> str:
        if self.is_executed:
            return TRANSFER_STATUS.executed
        elif self.is_failed:
            return TRANSFER_STATUS.failed
        elif self.is_canceled:
            return TRANSFER_STATUS.canceled
        elif self.is_processed:
            return TRANSFER_STATUS.processed
        else:
            return TRANSFER_STATUS.scheduled

    @property
    def is_canceled(self):
        return TransferCancellation.objects.filter(transfer=self).exists()

    @property
    def is_processed(self):
        return TransferReceipt.objects.filter(transfer=self).exists()

    @property
    def is_executed(self):
        return TransferExecution.objects.filter(transfer=self).exists()

    @property
    def is_failed(self):
        return TransferFailure.objects.filter(transfer=self).exists()

    @property
    def is_finalized(self) -> bool:
        return self.status != TRANSFER_STATUS.scheduled

    @property
    def target(self) -> Union[User, Address]:
        return self.receiver or self.address

    def get_executor(self):
        for executor_class in self.EXECUTORS:
            executor = executor_class.select_for_transfer(
                amount=self.as_token_amount, target=self.target
            )
            if executor:
                return executor

    def execute(self):
        if self.is_finalized:
            logger.warning(f"{self} is already finalized as {self.status}")
            return

        try:
            # The user has already been deducted from the transfer amount upon
            # creation. This check here just enforces that the transfer is not
            # doing double spend of reserved funds.
            sender_account_balance = self.sender.account.get_balance(token=self.currency)
            if sender_account_balance.amount < 0:
                raise TransferError("Insufficient balance")

            executor = self.get_executor()
            if not executor:
                raise TransferError("Could not get find a suitable method to execute transfer")

            executor.execute(self)
        except TransferError as exc:
            logger.info(f"{self} failed: {str(exc)}")
            TransferFailure.objects.create(transfer=self)
        except Exception as exc:
            TransferFailure.objects.create(transfer=self)
            logger.exception(exc)


class TransferReceipt(TimeStampedModel):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="receipt")
    network = models.CharField(max_length=64, choices=PAYMENT_NETWORKS)
    identifier = models.CharField(max_length=300, null=True)


class TransferExecution(TimeStampedModel):
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name="execution")


class BlockchainTransferExecution(TransferExecution):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    @property
    def fee(self) -> EthereumTokenAmount:
        ETH = EthereumToken.ETH(chain=self.transaction.block.chain)
        return ETH.from_wei(self.transaction.gas_fee)


class RaidenTransferExecution(TransferExecution):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)


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
    "RaidenTransferExecution",
    "TransferReceipt",
    "TransferError",
    "InternalTransferExecutor",
    "BlockchainTransferExecutor",
    "RaidenTransferExecutor",
]
