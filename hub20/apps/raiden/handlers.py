import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.raiden.models import Payment, TokenNetworkChannelStatus, TokenNetworkChannelEvent
from hub20.apps.raiden.signals import raiden_payment_received


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
