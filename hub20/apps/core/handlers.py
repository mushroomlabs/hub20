import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from psycopg2.extras import NumericRange

from hub20.apps.blockchain.models import Block, Chain, Transaction
from hub20.apps.blockchain.signals import (
    block_sealed,
    ethereum_node_connected,
    ethereum_node_disconnected,
    ethereum_node_sync_lost,
    ethereum_node_sync_recovered,
)
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.ethereum_money.signals import (
    account_deposit_received,
    incoming_transfer_broadcast,
    outgoing_transfer_mined,
)
from hub20.apps.raiden.models import Payment as RaidenNodePayment, Raiden
from hub20.apps.raiden.signals import raiden_payment_received

from . import tasks
from .choices import PAYMENT_METHODS
from .models import (
    BlockchainPayment,
    BlockchainPaymentRoute,
    BlockchainTransferExecution,
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
    TransferConfirmation,
    TransferFailure,
)
from .settings import app_settings
from .signals import payment_confirmed, payment_received

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


@receiver(ethereum_node_disconnected, sender=Chain)
@receiver(ethereum_node_sync_lost, sender=Chain)
def on_ethereum_node_error_send_open_checkout_events(sender, **kw):
    chain = kw["chain"]
    for checkout in Checkout.objects.filter(chain=chain).unpaid().with_blockchain_route():
        tasks.publish_checkout_event(
            checkout.id, event_data=CheckoutEvents.ETHEREUM_NODE_UNAVAILABLE.value
        )


@receiver(ethereum_node_connected, sender=Chain)
@receiver(ethereum_node_sync_recovered, sender=Chain)
def on_ethereum_node_ok_send_open_checkout_events(sender, **kw):
    chain = kw["chain"]
    for checkout in Checkout.objects.filter(chain=chain).unpaid().with_blockchain_route():
        tasks.publish_checkout_event(checkout.id, event_data=CheckoutEvents.ETHEREUM_NODE_OK.value)


@receiver(account_deposit_received, sender=Transaction)
def on_account_deposit_check_blockchain_payments(sender, **kw):
    account = kw["account"]
    amount = kw["amount"]
    transaction = kw["transaction"]

    orders = PaymentOrder.objects.with_blockchain_route(transaction.block.number)
    order = orders.filter(routes__blockchainpaymentroute__account=account).first()

    if not order:
        return

    route = BlockchainPaymentRoute.objects.filter(
        order=order, payment_window__contains=transaction.block.number
    ).first()

    payment = BlockchainPayment.objects.create(
        route=route, amount=amount.amount, currency=amount.currency, transaction=transaction
    )
    payment_received.send(sender=BlockchainPayment, payment=payment)


@receiver(incoming_transfer_broadcast, sender=EthereumToken)
def on_incoming_transfer_broadcast_sent_maybe_publish_checkout(sender, **kw):
    recipient = kw["account"]
    payment_amount = kw["amount"]
    tx_hash = kw["transaction_hash"]

    route = BlockchainPaymentRoute.objects.available().filter(account=recipient).first()

    if not route:
        return

    checkout = Checkout.objects.unpaid().with_blockchain_route().filter(routes=route).first()

    if not checkout:
        return

    tasks.publish_checkout_event.delay(
        checkout.pk,
        event=CheckoutEvents.BLOCKCHAIN_TRANSFER_BROADCAST.value,
        amount=payment_amount.amount,
        token=payment_amount.currency.address,
        identifier=tx_hash,
        payment_route=route.name,
    )


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

    confirmed_block = block_data.number - app_settings.Transfer.minimum_confirmations

    transfers_to_confirm = ExternalTransfer.unconfirmed.filter(
        execution__blockchaintransferexecution__transaction__block__number__lte=confirmed_block
    )

    for transfer in transfers_to_confirm:
        TransferConfirmation.objects.create(transfer=transfer)


@receiver(raiden_payment_received, sender=RaidenNodePayment)
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

        available_accounts = EthereumAccount.objects.exclude(
            blockchain_routes__payment_window__overlap=NumericRange(*payment_window)
        )

        account = available_accounts.order_by("?").first() or EthereumAccount.generate()
        account.blockchain_routes.create(order=order, payment_window=payment_window)
    else:
        logger.warning("Failed to create blockchain route. Chain data not synced")


@receiver(post_save, sender=PaymentOrder)
@receiver(post_save, sender=Checkout)
def on_order_created_set_raiden_route(sender, **kw):

    if not kw["created"]:
        return

    order = kw["instance"]
    raiden = Raiden.get()

    if raiden and raiden.open_channels.filter(token_network__token=order.currency).exists():
        raiden.payment_routes.create(order=order)


@receiver(block_sealed, sender=Block)
def on_block_sealed_check_confirmed_payments(sender, **kw):
    block_data = kw["block_data"]

    block_number_to_confirm = block_data.number - app_settings.Payment.minimum_confirmations

    if block_number_to_confirm >= 0:
        payments = BlockchainPayment.objects.all()

        for payment in payments.filter(transaction__block__number=block_number_to_confirm):
            if not payment.is_confirmed:
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
            route=route.account.address,
        )


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
        identifier=payment.transaction.hash_hex,
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
def on_transfer_created_schedule_execution(sender, **kw):
    transfer = kw["instance"]
    if kw["created"]:
        tasks.execute_transfer.delay(transfer.id)


@receiver(post_save, sender=TransferFailure)
@receiver(post_save, sender=TransferConfirmation)
def on_transfer_finalization_destroy_reserve(sender, **kw):
    final_event = kw["instance"]
    if kw["created"]:
        transfer = final_event.transfer
        try:
            transfer.reserve.delete()
        except Transfer.reserve.RelatedObjectDoesNotExist:
            pass
        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=Store)
def on_store_created_generate_key_pair(sender, **kw):
    store = kw["instance"]
    if kw["created"]:
        StoreRSAKeyPair.generate(store)


__all__ = [
    "on_ethereum_node_ok_send_open_checkout_events",
    "on_ethereum_node_error_send_open_checkout_events",
    "on_account_deposit_check_blockchain_payments",
    "on_incoming_transfer_broadcast_sent_maybe_publish_checkout",
    "on_raiden_payment_received_check_raiden_payments",
    "on_order_created_set_blockchain_route",
    "on_order_created_set_raiden_route",
    "on_block_added_publish_block_created_event",
    "on_block_added_publish_expired_blockchain_routes",
    "on_block_sealed_check_confirmed_payments",
    "on_block_sealed_check_confirmed_transfers",
    "on_blockchain_payment_received_maybe_publish_checkout",
    "on_blockchain_transfer_mined_record_execution",
    "on_payment_confirmed_set_credit",
    "on_payment_confirmed_publish_checkout",
    "on_transfer_created_schedule_execution",
    "on_transfer_finalization_destroy_reserve",
    "on_store_created_generate_key_pair",
]
