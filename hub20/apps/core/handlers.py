import datetime
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Block, Transaction
from hub20.apps.core import tasks
from hub20.apps.core.app_settings import PAYMENT_SETTINGS, TRANSFER_SETTINGS
from hub20.apps.core.choices import PAYMENT_EVENT_TYPES, PAYMENT_METHODS, TRANSFER_EVENT_TYPES
from hub20.apps.core.models import (
    BlockchainPayment,
    Checkout,
    ExternalTransfer,
    InternalPayment,
    InternalTransfer,
    PaymentOrder,
    PaymentOrderEvent,
    PaymentOrderMethod,
    RaidenPayment,
    Store,
    StoreRSAKeyPair,
    Transfer,
    Wallet,
)
from hub20.apps.core.signals import (
    blockchain_payment_sent,
    order_canceled,
    order_paid,
    payment_confirmed,
    payment_received,
    transfer_confirmed,
    transfer_executed,
    transfer_failed,
    transfer_scheduled,
)
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.ethereum_money.signals import account_deposit_received
from hub20.apps.raiden.models import Payment as RaidenPaymentEvent, Raiden
from hub20.apps.raiden.signals import raiden_payment_received

logger = logging.getLogger(__name__)


@receiver(account_deposit_received, sender=Transaction)
def on_account_deposit_check_blockchain_payments(sender, **kw):
    account = kw["account"]
    transaction = kw["transaction"]
    amount = kw["amount"]
    order = PaymentOrder.objects.filter(payment_method__wallet__account=account).first()

    if not order:
        return

    payment = BlockchainPayment.objects.create(
        order=order, amount=amount.amount, currency=amount.currency, transaction=transaction
    )
    payment_received.send(sender=BlockchainPayment, payment=payment)


@receiver(blockchain_payment_sent, sender=EthereumToken)
def on_blockchain_payment_sent_maybe_publish_checkout(sender, **kw):
    recipient_address = kw["recipient"]
    payment_amount = kw["amount"]
    tx_hash = kw["transaction_hash"]
    checkout = Checkout.objects.filter(
        payment_order__payment_method__wallet__account__address=recipient_address
    ).first()

    if not checkout:
        return

    if not checkout.payment_order.is_finalized:
        tasks.publish_checkout_event.delay(
            checkout.pk,
            event="payment.sent",
            amount=payment_amount.amount,
            token=payment_amount.currency.address,
            identifier=tx_hash,
            payment_method=PAYMENT_METHODS.blockchain,
        )


@receiver(raiden_payment_received, sender=RaidenPaymentEvent)
def on_raiden_payment_received_check_raiden_payments(sender, **kw):
    raiden_payment = kw["payment"]

    order = PaymentOrder.objects.filter(
        payment_method__identifier=raiden_payment.identifier,
        payment_method__raiden=raiden_payment.channel.raiden,
    ).first()

    if order is not None:
        amount = raiden_payment.as_token_amount
        payment = RaidenPayment.objects.create(
            order=order,
            amount=amount.amount,
            currency=raiden_payment.token,
            payment=raiden_payment,
        )
        payment_confirmed.send(sender=RaidenPayment, payment=payment)


@receiver(post_save, sender=PaymentOrder)
def on_order_created_set_payment_methods(sender, **kw):
    order = kw["instance"]
    if kw["created"]:
        unlocked_wallets = Wallet.objects.filter(paymentordermethod__isnull=True)
        wallet = unlocked_wallets.order_by("?").first() or Wallet.generate()

        raiden = Raiden.objects.filter(token_networks__token=order.currency).first()
        expiration_time = order.created + datetime.timedelta(
            seconds=PaymentOrderMethod.EXPIRATION_TIME
        )

        PaymentOrderMethod.objects.create(
            order=order, wallet=wallet, raiden=raiden, expiration_time=expiration_time
        )


@receiver(post_save, sender=PaymentOrder)
def on_payment_created_set_created_status(sender, **kw):
    payment = kw["instance"]
    if payment.created:
        payment.events.create(status=PAYMENT_EVENT_TYPES.requested)


@receiver(post_save, sender=PaymentOrderMethod)
def on_payment_order_method_created_schedule_expiration_task(sender, **kw):
    payment_method = kw["instance"]
    if kw["created"]:

        tasks.expire_payment_method.apply_async(
            args=(payment_method.id,), eta=payment_method.expiration_time
        )


@receiver(post_save, sender=PaymentOrderEvent)
def on_payment_event_created_send_order_paid_signal(sender, **kw):
    payment_event = kw["instance"]
    if payment_event.created and payment_event.status == PAYMENT_EVENT_TYPES.confirmed:
        order_paid.send(sender=PaymentOrder, payment_order=payment_event.order)


@receiver(post_save, sender=PaymentOrderEvent)
def on_payment_order_canceled_event_send_order_canceled_signal(sender, **kw):
    payment_event = kw["instance"]
    if payment_event.created and payment_event.status == PAYMENT_EVENT_TYPES.canceled:
        order_canceled.send(sender=PaymentOrder, payment_order=payment_event.order)


@receiver(post_save, sender=PaymentOrderEvent)
def on_payment_order_expired_event_maybe_publish_checkout(sender, **kw):
    payment_event = kw["instance"]
    created = kw["created"]
    if created and payment_event.status == PAYMENT_EVENT_TYPES.expired:
        checkout = Checkout.objects.filter(payment_order=payment_event.order).first()
        if checkout:
            tasks.publish_checkout_event.delay(checkout.pk, event="checkout.expired")


@receiver(post_save, sender=Block)
def on_block_added_check_confirmed_payments(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    block_number_to_confirm = block.number - PAYMENT_SETTINGS.minimum_confirmations
    if created and block_number_to_confirm >= 0:
        payments = BlockchainPayment.objects.all()

        for payment in payments.filter(
            transaction__block__number=block_number_to_confirm,
            transaction__block__chain=block.chain,
        ):
            logger.info(f"Confirming {payment}")
            payment_confirmed.send(sender=BlockchainPayment, payment=payment)


@receiver(post_save, sender=Block)
def on_block_added_check_confirmed_transfers(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    block_number_to_confirm = block.number - TRANSFER_SETTINGS.minimum_confirmations
    if created and block_number_to_confirm >= 0:
        transactions = Transaction.objects.filter(
            block__number=block_number_to_confirm, block__chain=block.chain
        )

        tx_hashes = transactions.values_list("hash", flat=True)
        transfers = ExternalTransfer.objects.all()
        for transfer in transfers.filter(chain_transaction__transaction_hash__in=tx_hashes):
            logger.info(f"Confirming {transfer}")
            transfer_confirmed.send(sender=ExternalTransfer, transfer=transfer)


@receiver(payment_received, sender=InternalPayment)
@receiver(payment_received, sender=BlockchainPayment)
def on_payment_received_update_status(sender, **kw):
    payment = kw["payment"]
    logger.info(f"Processing payment {payment} received")
    payment.order.update_status()
    payment.order.maybe_finalize()


@receiver(payment_received, sender=BlockchainPayment)
def on_blockchain_payment_received_maybe_publish_checkout(sender, **kw):
    payment = kw["payment"]

    checkouts = Checkout.objects.filter(payment_order__payment=payment)
    checkout_id = checkouts.values_list("id", flat=True).first()

    if checkout_id is None:
        return

    tasks.publish_checkout_event.delay(
        checkout_id,
        amount=payment.amount,
        token=payment.currency.address,
        identifier=payment.transaction.hash.hex(),
        payment_method=PAYMENT_METHODS.blockchain,
        event="payment.received",
    )


@receiver(payment_confirmed, sender=InternalPayment)
@receiver(payment_confirmed, sender=BlockchainPayment)
@receiver(payment_confirmed, sender=RaidenPayment)
def on_payment_confirmed_publish_checkout(sender, **kw):
    payment = kw["payment"]

    checkouts = Checkout.objects.filter(payment_order__payment=payment)
    checkout_id = checkouts.values_list("id", flat=True).first()

    payment_method = {
        InternalPayment: PAYMENT_METHODS.internal,
        BlockchainPayment: PAYMENT_METHODS.blockchain,
        RaidenPayment: PAYMENT_METHODS.raiden,
    }.get(sender)

    if checkout_id is None:
        return

    tasks.publish_checkout_event.delay(
        checkout_id,
        amount=payment.amount,
        token=payment.currency.address,
        event="payment.confirmed",
        payment_method=payment_method,
    )


@receiver(payment_confirmed, sender=BlockchainPayment)
@receiver(payment_confirmed, sender=RaidenPayment)
def on_payment_confirmed_finalize(sender, **kw):
    payment = kw["payment"]
    logger.info(f"Processing payment {payment} confirmed")
    payment.order.maybe_finalize()


@receiver(order_paid, sender=PaymentOrder)
def on_order_paid_credit_user(sender, **kw):
    order = kw["payment_order"]

    order.user.balance_entries.create(amount=order.amount, currency=order.currency)


@receiver(order_paid, sender=PaymentOrder)
@receiver(order_canceled, sender=PaymentOrder)
def on_order_finalized_free_payment_channels(sender, **kw):
    order = kw["payment_order"]

    try:
        order.payment_method.delete()
    except PaymentOrder.payment_method.RelatedObjectDoesNotExist:
        pass
    except Exception as exc:
        logger.exception(exc)


@receiver(post_save, sender=InternalTransfer)
@receiver(post_save, sender=ExternalTransfer)
def on_transfer_created_mark_transfer_scheduled(sender, **kw):
    transfer = kw["instance"]
    if kw["created"]:
        transfer.events.create(status=TRANSFER_EVENT_TYPES.scheduled)
        tasks.execute_transfer.delay(transfer.id)
        transfer_scheduled.send(sender=sender, transfer=transfer)


@receiver(transfer_failed, sender=Transfer)
def on_transfer_failed_mark_as_failed(sender, **kw):
    transfer = kw["transfer"]
    transfer.events.create(status=TRANSFER_EVENT_TYPES.failed)


@receiver(transfer_confirmed, sender=ExternalTransfer)
@receiver(transfer_confirmed, sender=InternalTransfer)
def on_transfer_confirmed_mark_as_confirmed(sender, **kw):
    transfer = kw["transfer"]
    transfer.events.create(status=TRANSFER_EVENT_TYPES.confirmed)


@receiver(transfer_executed, sender=ExternalTransfer)
def on_external_transfer_executed_mark_as_executed(sender, **kw):
    transfer = kw["transfer"]
    transfer.events.create(status=TRANSFER_EVENT_TYPES.executed)


@receiver(transfer_confirmed, sender=ExternalTransfer)
def on_external_transfer_confirmed_destroy_reserve(sender, **kw):
    transfer = kw["transfer"]
    try:
        transfer.reserve.delete()
    except Transfer.reserve.RelatedObjectDoesNotExist:
        pass
    except Exception as exc:
        logger.exception(exc)


@receiver(transfer_confirmed, sender=InternalTransfer)
def on_internal_transfer_confirmed_move_balances(sender, **kw):
    transfer = kw["transfer"]
    transfer.receiver.balance_entries.create(amount=transfer.amount, currency=transfer.currency)
    transfer.sender.balance_entries.create(amount=-transfer.amount, currency=transfer.currency)


@receiver(post_save, sender=Store)
def on_store_created_generate_key_pair(sender, **kw):
    store = kw["instance"]
    if kw["created"]:
        StoreRSAKeyPair.generate(store)


__all__ = [
    "on_account_deposit_check_blockchain_payments",
    "on_blockchain_payment_sent_maybe_publish_checkout",
    "on_blockchain_payment_received_maybe_publish_checkout",
    "on_block_added_check_confirmed_payments",
    "on_block_added_check_confirmed_transfers",
    "on_payment_created_set_created_status",
    "on_payment_order_method_created_schedule_expiration_task",
    "on_payment_event_created_send_order_paid_signal",
    "on_payment_order_expired_event_maybe_publish_checkout",
    "on_payment_received_update_status",
    "on_payment_confirmed_finalize",
    "on_payment_confirmed_publish_checkout",
    "on_payment_order_canceled_event_send_order_canceled_signal",
    "on_order_paid_credit_user",
    "on_order_finalized_free_payment_channels",
    "on_order_created_set_payment_methods",
    "on_transfer_created_mark_transfer_scheduled",
    "on_transfer_failed_mark_as_failed",
    "on_transfer_confirmed_mark_as_confirmed",
    "on_internal_transfer_confirmed_move_balances",
    "on_external_transfer_executed_mark_as_executed",
    "on_external_transfer_confirmed_destroy_reserve",
    "on_store_created_generate_key_pair",
]
