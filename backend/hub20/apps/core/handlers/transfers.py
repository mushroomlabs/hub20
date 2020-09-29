import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Block, Transaction
from hub20.apps.blockchain.signals import block_sealed
from hub20.apps.core import tasks
from hub20.apps.core.models import (
    BlockchainTransferExecution,
    ExternalTransfer,
    InternalTransfer,
    TransferConfirmation,
    TransferExecution,
    TransferFailure,
)
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money.signals import outgoing_transfer_mined

logger = logging.getLogger(__name__)


def _check_for_blockchain_transfer_confirmations(block_number):
    confirmed_block = block_number - app_settings.Transfer.minimum_confirmations

    transfers_to_confirm = ExternalTransfer.unconfirmed.filter(
        execution__blockchaintransferexecution__transaction__block__number__lte=confirmed_block
    )

    for transfer in transfers_to_confirm:
        TransferConfirmation.objects.create(transfer=transfer)


@receiver(outgoing_transfer_mined, sender=Transaction)
def on_blockchain_transfer_mined_record_execution(sender, **kw):
    amount = kw["amount"]
    transaction = kw["transaction"]
    recipient_address = kw["recipient_address"]

    transfer = ExternalTransfer.objects.filter(
        execution__isnull=True,
        amount=amount.amount,
        currency=amount.currency,
        recipient_address=recipient_address,
    ).first()

    if transfer:
        BlockchainTransferExecution.objects.create(transfer=transfer, transaction=transaction)


@receiver(block_sealed, sender=Block)
def on_block_sealed_check_confirmed_transfers(sender, **kw):
    block_data = kw["block_data"]

    _check_for_blockchain_transfer_confirmations(block_data.number)


@receiver(post_save, sender=Block)
def on_block_created_check_confirmed_transfers(sender, **kw):
    if kw["created"]:
        block = kw["instance"]
        _check_for_blockchain_transfer_confirmations(block.number)


@receiver(post_save, sender=InternalTransfer)
@receiver(post_save, sender=ExternalTransfer)
def on_transfer_created_schedule_execution(sender, **kw):
    if kw["created"]:
        transfer = kw["instance"]
        tasks.execute_transfer.delay(transfer.id)


@receiver(post_save, sender=TransferFailure)
def on_transfer_failure_revert(sender, **kw):
    if kw["created"]:
        failure = kw["instance"]
        transfer = failure.transfer

        if hasattr(transfer, "execution"):
            transfer.execution.delete()

        if hasattr(transfer, "confirmation"):
            transfer.confirmation.delete()


__all__ = [
    "on_block_created_check_confirmed_transfers",
    "on_block_sealed_check_confirmed_transfers",
    "on_blockchain_transfer_mined_record_execution",
    "on_transfer_created_schedule_execution",
    "on_transfer_failure_revert",
]
