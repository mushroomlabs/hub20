import logging

from django.db.models.signals import post_save
from django.dispatch import receiver


from raiden.models import Payment
from raiden.signals import raiden_payment_received


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def on_payment_created_check_received(sender, **kw):
    payment = kw["instance"]
    if kw["created"]:
        if payment.receiver_address == payment.channel.raiden.address:
            logger.info(f"New payment received by {payment.channel}")
            raiden_payment_received.send(sender=Payment, payment=payment)
