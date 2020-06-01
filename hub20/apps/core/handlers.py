import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from psycopg2.extras import NumericRange

from hub20.apps.blockchain.models import Block, Chain, Transaction
from hub20.apps.blockchain.signals import (
    blockchain_node_connected,
    blockchain_node_disconnected,
    blockchain_node_sync_lost,
    blockchain_node_sync_recovered,
)
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.ethereum_money.signals import account_deposit_received
from hub20.apps.ethereum_wallet.models import Wallet
from hub20.apps.raiden.models import Payment as RaidenPaymentEvent, Raiden
from hub20.apps.raiden.signals import raiden_payment_received

from . import tasks
from .choices import PAYMENT_METHODS, TRANSFER_EVENT_TYPES
from .models import (
    BlockchainPayment,
    BlockchainPaymentRoute,
    Checkout,
    CheckoutEvents,
    ExternalTransfer,
    InternalPayment,
    InternalTransfer,
    PaymentCredit,
    PaymentOrder,
    RaidenPayment,
    RaidenPaymentRoute,
    Store,
    StoreRSAKeyPair,
    Transfer,
)
from .settings import app_settings
from .signals import (
    blockchain_payment_sent,
    payment_confirmed,
    payment_received,
    transfer_confirmed,
    transfer_executed,
    transfer_failed,
    transfer_scheduled,
)

logger = logging.getLogger(__name__)


@receiver(blockchain_node_disconnected, sender=Chain)
@receiver(blockchain_node_sync_lost, sender=Chain)
def on_blockchain_node_error_send_open_checkout_events(sender, **kw):
    chain = kw["chain"]
    for checkout in Checkout.objects.filter(chain=chain).unpaid().with_blockchain_route():
        tasks.publish_checkout_event(
            checkout.id, event_data=CheckoutEvents.BLOCKCHAIN_NODE_UNAVAILABLE.value
        )


@receiver(blockchain_node_connected, sender=Chain)
@receiver(blockchain_node_sync_recovered, sender=Chain)
def on_blockchain_node_ok_send_open_checkout_events(sender, **kw):
    chain = kw["chain"]
    for checkout in Checkout.objects.filter(chain=chain).unpaid().with_blockchain_route():
        tasks.publish_checkout_event(
            checkout.id, event_data=CheckoutEvents.BLOCKCHAIN_NODE_OK.value
        )


@receiver(account_deposit_received, sender=Transaction)
def on_account_deposit_check_blockchain_payments(sender, **kw):
    account = kw["account"]
    transaction = kw["transaction"]
    amount = kw["amount"]

    orders = PaymentOrder.objects.with_blockchain_route(transaction.block.number)
    order = orders.filter(routes__blockchainpaymentroute__wallet__account=account).first()

    if not order:
        return

    route = BlockchainPaymentRoute.objects.filter(
        order=order, payment_window__contains=transaction.block.number
    ).first()

    payment = BlockchainPayment.objects.create(
        route=route, amount=amount.amount, currency=amount.currency, transaction=transaction
    )
    payment_received.send(sender=BlockchainPayment, payment=payment)


@receiver(blockchain_payment_sent, sender=EthereumToken)
def on_blockchain_payment_sent_maybe_publish_checkout(sender, **kw):
    recipient_address = kw["recipient"]
    payment_amount = kw["amount"]
    tx_hash = kw["transaction_hash"]
    chain = Chain.make()
    current_block = chain.highest_block

    blockchain_payment_route = BlockchainPaymentRoute.objects.filter(
        wallet__account__address=recipient_address, payment_window__contains=current_block
    ).first()

    if not blockchain_payment_route:
        return

    checkout = Checkout.objects.filter(
        routes__blockchainpaymentroute=blockchain_payment_route
    ).first()

    if not checkout:
        return

    tasks.publish_checkout_event.delay(
        checkout.pk,
        event=CheckoutEvents.BLOCKCHAIN_TRANSFER_BROADCAST.value,
        amount=payment_amount.amount,
        token=payment_amount.currency.address,
        identifier=tx_hash,
        payment_route=blockchain_payment_route.name,
    )


@receiver(raiden_payment_received, sender=RaidenPaymentEvent)
def on_raiden_payment_received_check_raiden_payments(sender, **kw):
    raiden_payment = kw["payment"]

    payment_route = RaidenPaymentRoute.objects.filter(
        identifier=raiden_payment.identifier, raiden=raiden_payment.channel.raiden,
    ).first()

    if payment_route is not None:
        amount = raiden_payment.as_token_amount
        payment = RaidenPayment.objects.create(
            route=payment_route,
            amount=amount.amount,
            currency=raiden_payment.token,
            payment=raiden_payment,
        )
        payment_confirmed.send(sender=RaidenPayment, payment=payment)


@receiver(post_save, sender=PaymentOrder)
@receiver(post_save, sender=Checkout)
def on_order_created_set_blockchain_route(sender, **kw):

    if not kw["created"]:
        return

    order = kw["instance"]
    if order.chain.synced:
        current_block = order.chain.highest_block
        expiration_block = current_block + app_settings.Payment.blockchain_route_lifetime

        payment_window = (current_block, expiration_block)

        available_wallets = Wallet.objects.exclude(
            payment_routes__payment_window__overlap=NumericRange(*payment_window)
        )

        wallet = available_wallets.order_by("?").first() or Wallet.generate()
        BlockchainPaymentRoute.objects.create(
            order=order, wallet=wallet, payment_window=payment_window
        )
    else:
        logger.warning("Failed to create blockchain route. Chain data not synced")


@receiver(post_save, sender=PaymentOrder)
@receiver(post_save, sender=Checkout)
def on_order_created_set_raiden_route(sender, **kw):

    if not kw["created"]:
        return

    order = kw["instance"]
    raiden = Raiden.objects.filter(token_networks__token=order.currency).first()

    if raiden:
        raiden.payment_routes.create(order=order)


@receiver(post_save, sender=Block)
def on_block_added_check_confirmed_payments(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    block_number_to_confirm = block.number - app_settings.Payment.minimum_confirmations

    if created and block_number_to_confirm >= 0:
        payments = BlockchainPayment.objects.all()

        for payment in payments.filter(
            transaction__block__number=block_number_to_confirm,
            transaction__block__chain=block.chain,
        ):
            logger.info(f"Confirming {payment}")
            payment_confirmed.send(sender=BlockchainPayment, payment=payment)


@receiver(post_save, sender=Block)
def on_block_added_publish_block_created_event(sender, **kw):
    block = kw["instance"]

    for checkout in Checkout.objects.unpaid().with_blockchain_route(block.number):
        tasks.publish_checkout_event.delay(
            checkout.id, event=CheckoutEvents.BLOCKCHAIN_BLOCK_CREATED.value, block=block.number
        )


@receiver(post_save, sender=Block)
def on_block_added_publish_expired_blockchain_routes(sender, **kw):
    block = kw["instance"]

    expiring_routes = BlockchainPaymentRoute.objects.filter(
        payment_window__endswith=block.number - 1
    )

    for route in expiring_routes:
        tasks.publish_checkout_event.delay(
            route.order_id,
            event=CheckoutEvents.BLOCKCHAIN_ROUTE_EXPIRED.value,
            route=route.wallet.address,
        )


@receiver(post_save, sender=Block)
def on_block_added_check_confirmed_transfers(sender, **kw):
    block = kw["instance"]
    created = kw["created"]

    block_number_to_confirm = block.number - app_settings.Transfer.minimum_confirmations
    if created and block_number_to_confirm >= 0:
        transactions = Transaction.objects.filter(
            block__number=block_number_to_confirm, block__chain=block.chain
        )

        tx_hashes = transactions.values_list("hash", flat=True)
        transfers = ExternalTransfer.objects.all()
        for transfer in transfers.filter(chain_transaction__transaction_hash__in=tx_hashes):
            logger.info(f"Confirming {transfer}")
            transfer_confirmed.send(sender=ExternalTransfer, transfer=transfer)


@receiver(payment_received, sender=BlockchainPayment)
def on_blockchain_payment_received_maybe_publish_checkout(sender, **kw):
    payment = kw["payment"]

    checkout = Checkout.objects.filter(routes__payment=payment).first()

    if not checkout:
        return

    tasks.publish_checkout_event.delay(
        checkout.id,
        amount=payment.amount,
        token=payment.currency.address,
        identifier=payment.transaction.hash.hex(),
        payment_method=PAYMENT_METHODS.blockchain,
        event="payment.received",
    )


@receiver(payment_confirmed, sender=InternalPayment)
@receiver(payment_confirmed, sender=BlockchainPayment)
@receiver(payment_confirmed, sender=RaidenPayment)
def on_payment_confirmed_set_credit(sender, **kw):
    payment = kw["payment"]

    PaymentCredit.objects.get_or_create(
        payment=payment,
        defaults={
            "user": payment.route.order.user,
            "currency": payment.currency,
            "amount": payment.amount,
        },
    )


@receiver(payment_confirmed, sender=InternalPayment)
@receiver(payment_confirmed, sender=BlockchainPayment)
@receiver(payment_confirmed, sender=RaidenPayment)
def on_payment_confirmed_publish_checkout(sender, **kw):
    payment = kw["payment"]

    checkouts = Checkout.objects.filter(routes__payment=payment)
    checkout_id = checkouts.values_list("id", flat=True).first()

    if checkout_id is None:
        return

    payment_method = {
        InternalPayment: PAYMENT_METHODS.internal,
        BlockchainPayment: PAYMENT_METHODS.blockchain,
        RaidenPayment: PAYMENT_METHODS.raiden,
    }.get(sender)

    tasks.publish_checkout_event.delay(
        checkout_id,
        amount=payment.amount,
        token=payment.currency.address,
        event="payment.confirmed",
        payment_method=payment_method,
    )


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
    "on_blockchain_node_ok_send_open_checkout_events",
    "on_blockchain_node_error_send_open_checkout_events",
    "on_account_deposit_check_blockchain_payments",
    "on_blockchain_payment_sent_maybe_publish_checkout",
    "on_raiden_payment_received_check_raiden_payments",
    "on_order_created_set_blockchain_route",
    "on_order_created_set_raiden_route",
    "on_block_added_publish_block_created_event",
    "on_block_added_publish_expired_blockchain_routes",
    "on_block_added_check_confirmed_payments",
    "on_block_added_check_confirmed_transfers",
    "on_blockchain_payment_received_maybe_publish_checkout",
    "on_payment_confirmed_set_credit",
    "on_payment_confirmed_publish_checkout",
    "on_transfer_created_mark_transfer_scheduled",
    "on_transfer_failed_mark_as_failed",
    "on_transfer_confirmed_mark_as_confirmed",
    "on_external_transfer_executed_mark_as_executed",
    "on_external_transfer_confirmed_destroy_reserve",
    "on_internal_transfer_confirmed_move_balances",
    "on_store_created_generate_key_pair",
]
