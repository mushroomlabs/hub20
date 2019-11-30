import datetime
import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal
from django.utils import timezone

from blockchain.models import Block, Transaction
from .. import app_settings
from .payments import Invoice, BlockchainPayment

logger = logging.getLogger(__name__)

payment_received = Signal(providing_args=["payment"])
payment_confirmed = Signal(providing_args=["payment"])


@receiver(pre_save, sender=Invoice)
def on_invoice_created(sender, **kw):
    instance = kw["instance"]
    created_time = instance.created or timezone.now()
    if instance.expiration_time is None:
        instance.expiration_time = created_time + datetime.timedelta(
            seconds=Invoice.EXPIRATION_TIME
        )


@receiver(post_save, sender=Transaction)
def on_transaction_mined(sender, **kw):
    instance = kw["instance"]
    created = kw["created"]

    if created:
        for payment in BlockchainPayment.objects.filter(transaction_hash=instance.hash):
            logger.info(f"Payment {payment} received on transaction {instance}")
            payment_received.send(sender=BlockchainPayment, payment=payment)


@receiver(post_save, sender=Block)
def on_block_added(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    if created:
        logger.info(f"Block {block} created")
        block_number_to_confirm = max(
            block.number - app_settings.PAYMENTS.minimum_confirmations, 0
        )

        transactions = Transaction.objects.filter(
            block__number=block_number_to_confirm, block__chain=block.chain
        )
        tx_hashes = transactions.values_list("hash", flat=True)
        for payment in BlockchainPayment.objects.filter(transaction_hash__in=tx_hashes):
            logger.info(f"Confirming {payment}")
            payment_confirmed.send(sender=BlockchainPayment, payment=payment)


@receiver(payment_received, sender=BlockchainPayment)
def on_blockchain_payment_received(sender, **kw):
    payment = kw["payment"]

    logger.info(f"Processing payment {payment} received")
    if payment.invoice.paid:
        payment.invoice.wallet.unlock()


__all__ = [
    "payment_received",
    "payment_confirmed",
    "on_invoice_created",
    "on_transaction_mined",
    "on_block_added",
    "on_blockchain_payment_received",
]
