import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Transaction
from hub20.apps.raiden.models import (
    ChannelDepositOrder,
    ChannelWithdrawOrder,
    Payment,
    RaidenManagementOrderResult,
    TokenNetworkChannelEvent,
    TokenNetworkChannelStatus,
    UserDepositContractOrder,
)
from hub20.apps.raiden.signals import raiden_payment_received, service_deposit_sent

from . import tasks

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


@receiver(post_save, sender=ChannelDepositOrder)
def on_channel_deposit_order_schedule_task(sender, **kw):
    deposit_order = kw["instance"]

    if kw["created"]:
        tasks.make_channel_deposit.delay(order_id=deposit_order.id)


@receiver(post_save, sender=ChannelWithdrawOrder)
def on_channel_withdraw_order_schedule_task(sender, **kw):
    withdraw_order = kw["instance"]

    if kw["created"]:
        tasks.make_channel_withdraw.delay(order_id=withdraw_order.id)


@receiver(post_save, sender=UserDepositContractOrder)
def on_service_deposit_created_schedule_task(sender, **kw):
    deposit_order = kw["instance"]

    if kw["created"]:
        tasks.make_udc_deposit.delay(order_id=deposit_order.id)


@receiver(service_deposit_sent, sender=Transaction)
def on_service_deposit_transaction_create_record(sender, **kw):
    deposit_amount = kw["amount"]

    order = UserDepositContractOrder.objects.filter(
        amount=deposit_amount.amount, currency=deposit_amount.currency, result__isnull=True,
    ).first()

    if not order:
        return

    RaidenManagementOrderResult.objects.create(
        transaction=kw["transaction"], raiden=kw["raiden"], order=order
    )


__all__ = [
    "on_payment_created_check_received",
    "on_token_network_channel_event_set_status",
    "on_channel_deposit_order_schedule_task",
    "on_channel_withdraw_order_schedule_task",
    "on_service_deposit_created_schedule_task",
    "on_service_deposit_transaction_create_record",
]
