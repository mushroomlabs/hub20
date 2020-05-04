import logging
from concurrent.futures import TimeoutError
from typing import List

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from ethtoken.abi import EIP20_ABI
from web3.exceptions import TransactionNotFound

from hub20.apps.blockchain.models import make_web3
from hub20.apps.ethereum_money.models import EthereumToken

from .consumers import CheckoutConsumer
from .models import PaymentOrderEvent, PaymentOrderMethod, Transfer
from .signals import blockchain_payment_sent

logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    transfer = Transfer.objects.get_subclass(id=transfer_id)
    transfer.execute()


@shared_task
def expire_payment_method(payment_method_id):

    payment_method = PaymentOrderMethod.objects.filter(id=payment_method_id).first()

    if not payment_method:
        return

    if payment_method.expiration_time >= timezone.now():
        return

    with transaction.atomic():
        order = payment_method.order
        if not order.is_finalized:
            order.events.create(status=PaymentOrderEvent.STATUS.expired)
        payment_method.delete()


@shared_task
def check_transaction_for_erc20_transfer(
    tx_hash: str, wallet_addresses: List[str], token_addresses: List[str]
):
    w3 = make_web3()
    chain_id = int(w3.net.version)

    try:
        tx = w3.eth.getTransaction(tx_hash)
        tokens = EthereumToken.objects.filter(chain=chain_id, address__in=token_addresses)
        for token in tokens:
            logger.info(f"Processing {token.code} transaction: {tx_hash}")
            contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
            fn, args = contract.decode_function_input(tx.input)

            # TODO: is this really the best way to identify the function?
            if fn.function_identifier == contract.functions.transfer.function_identifier:
                recipient = args["_to"]

                if recipient in wallet_addresses:
                    blockchain_payment_sent.send(
                        sender=EthereumToken,
                        recipient=recipient,
                        amount=token.from_wei(args["_value"]),
                        transaction_hash=tx_hash,
                    )

    except TimeoutError:
        logger.error(f"Failed request to get or check {tx_hash}")
    except TransactionNotFound:
        logger.info(f"Tx {tx_hash} has not yet been mined")
    except ValueError as exc:
        logger.error(str(exc))
    except Exception as exc:
        logger.exception(exc)


@shared_task
def check_transaction_for_eth_transfer(tx_hash: str, wallet_addresses: List[str]):
    w3 = make_web3()
    chain_id = int(w3.net.version)

    try:
        tx = w3.eth.getTransaction(tx_hash)

        if tx.to in wallet_addresses:
            ETH = EthereumToken.ETH(chain_id)
            blockchain_payment_sent.send(
                sender=EthereumToken,
                recipient=tx.to,
                amount=ETH.from_wei(tx.value),
                transaction_hash=tx_hash,
            )

    except TimeoutError:
        logger.warn(f"Failed request to get {tx_hash}")
    except TransactionNotFound:
        logger.info(f"Tx {tx_hash} has not yet been mined")
    except ValueError as exc:
        logger.error(str(exc))
    except Exception as exc:
        logger.exception(exc)


@shared_task
def publish_checkout_event(checkout_id, event="checkout.event", **event_data):
    layer = get_channel_layer()
    channel_group_name = CheckoutConsumer.get_group_name(checkout_id)

    logger.info(f"Publishing event {event}. Data: {event_data}")

    event_data.update({"type": "publish_payment_event", "event_name": event})

    async_to_sync(layer.group_send)(channel_group_name, event_data)
