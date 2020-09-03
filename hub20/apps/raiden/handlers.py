import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Transaction
from hub20.apps.raiden.models import (
    Payment,
    ServiceDeposit,
    TokenNetworkChannelEvent,
    TokenNetworkChannelStatus,
)
from hub20.apps.raiden.signals import raiden_payment_received, service_deposit_sent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def on_payment_created_check_received(sender, **kw):
    payment = kw["instance"]
    if kw["created"]:
        if payment.receiver_address == payment.channel.raiden.address:
            logger.info(f"New payment received by {payment.channel}")
            raiden_payment_received.send(sender=Payment, payment=payment)


@receiver(post_save, sender=TokenNetworkChannelEvent)
def on_token_network_channel_event_set_status(sender, **kw):
    event = kw["instance"]
    if kw["created"]:
        TokenNetworkChannelStatus.set_status(event.channel)


@receiver(service_deposit_sent, sender=Transaction)
def on_service_deposit_transaction_create_record(sender, **kw):
    deposit_amount = kw["amount"]

    ServiceDeposit.objects.create(
        transaction=kw["transaction"],
        raiden=kw["raiden"],
        amount=deposit_amount.amount,
        currency=deposit_amount.currency,
    )


__all__ = [
    "on_payment_created_check_received",
    "on_token_network_channel_event_set_status",
    "on_service_deposit_transaction_create_record",
]
