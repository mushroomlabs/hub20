import datetime
import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from blockchain.models import Block, Transaction
from hub20.app_settings import PAYMENT_SETTINGS
from hub20.choices import PAYMENT_STATUS
from hub20.models.accounting import BalanceEntry
from hub20.models.payments import Payment, BlockchainTransfer, InternalTransfer, PaymentLog
from hub20.signals import transfer_received, transfer_confirmed, payment_confirmed

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Payment)
def set_payment_expiration(sender, **kw):
    payment = kw["instance"]
    created_time = payment.created or timezone.now()
    payment.expiration_time = created_time + datetime.timedelta(seconds=Payment.EXPIRATION_TIME)


@receiver(post_save, sender=Payment)
def on_payment_created(sender, **kw):
    payment = kw["instance"]
    if payment.created:
        payment.logs.create(status=PAYMENT_STATUS.requested)


@receiver(post_save, sender=PaymentLog)
def on_payment_event(sender, **kw):
    payment_log = kw["instance"]
    if payment_log.created and payment_log.status == PAYMENT_STATUS.confirmed:
        payment_confirmed.send(sender=Payment, payment=payment_log.payment)


@receiver(post_save, sender=Transaction)
def on_transaction_mined(sender, **kw):
    instance = kw["instance"]
    created = kw["created"]

    if created:
        for transfer in BlockchainTransfer.objects.filter(transaction_hash=instance.hash):
            logger.info(f"Transfer {transfer} received on transaction {instance}")
            transfer_received.send(sender=BlockchainTransfer, transfer=transfer)


@receiver(post_save, sender=Block)
def on_block_added(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    if created:
        logger.info(f"Block {block} created")
        block_number_to_confirm = max(block.number - PAYMENT_SETTINGS.minimum_confirmations, 0)

        transactions = Transaction.objects.filter(
            block__number=block_number_to_confirm, block__chain=block.chain
        )
        tx_hashes = transactions.values_list("hash", flat=True)
        for transfer in BlockchainTransfer.objects.filter(transaction_hash__in=tx_hashes):
            logger.info(f"Confirming {transfer}")
            transfer_confirmed.send(sender=BlockchainTransfer, transfer=transfer)


@receiver(transfer_received, sender=InternalTransfer)
@receiver(transfer_received, sender=BlockchainTransfer)
def on_transfer_received(sender, **kw):
    transfer = kw["transfer"]
    logger.info(f"Processing transfer {transfer} received")
    transfer.payment.update_status()
    transfer.payment.maybe_finalize()


@receiver(transfer_confirmed, sender=BlockchainTransfer)
def on_transfer_confirmed(sender, **kw):
    transfer = kw["transfer"]
    logger.info(f"Processing transfer {transfer} confirmed")
    transfer.payment.maybe_finalize()


@receiver(payment_confirmed, sender=Payment)
def credit_payment(sender, **kw):
    payment = kw["payment"]

    BalanceEntry.objects.create(
        user=payment.user, amount=payment.amount, currency=payment.currency
    )


__all__ = [
    "on_payment_created",
    "on_transaction_mined",
    "on_block_added",
    "on_transfer_received",
    "on_transfer_confirmed",
    "set_payment_expiration",
]
