import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Transaction
from hub20.apps.core.models import BlockchainTransferExecution, RaidenTransferExecution, Transfer
from hub20.apps.ethereum_money.signals import outgoing_transfer_mined
from hub20.apps.raiden.models import Payment

logger = logging.getLogger(__name__)


@receiver(outgoing_transfer_mined, sender=Transaction)
def on_blockchain_transfer_mined_record_execution(sender, **kw):
    amount = kw["amount"]
    transaction = kw["transaction"]
    address = kw["address"]

    transfer = Transfer.processed.filter(
        amount=amount.amount,
        currency=amount.currency,
        address=address,
        receipt__identifier=transaction.hash_hex,
    ).first()

    if transfer:
        BlockchainTransferExecution.objects.create(transfer=transfer, transaction=transaction)


@receiver(post_save, sender=Payment)
def on_raiden_payment_sent_record_execution(sender, **kw):
    if kw["created"]:
        payment = kw["instance"]
        transfer = Transfer.processed.filter(
            amount=payment.amount,
            currency=payment.token,
            address=payment.receiver_address,
            receipt__identifier=payment.identifier,
        ).first()

        if transfer:
            RaidenTransferExecution.objects.create(transfer=transfer, payment=payment)


__all__ = [
    "on_blockchain_transfer_mined_record_execution",
    "on_raiden_payment_sent_record_execution",
]
