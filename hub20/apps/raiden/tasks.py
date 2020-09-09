import logging
from concurrent.futures import TimeoutError
from typing import Optional

from celery import shared_task
from web3 import Web3

from hub20.apps.blockchain.client import get_block_by_hash, get_transaction_by_hash, get_web3
from hub20.apps.blockchain.models import Block
from hub20.apps.ethereum_money.client import get_account_balance
from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.raiden import models
from hub20.apps.raiden.client.blockchain import get_service_token, make_service_deposit
from hub20.apps.raiden.client.node import RaidenClient

logger = logging.getLogger(__name__)


def _get_channel_from_event(token_network, event) -> Optional[models.TokenNetworkChannel]:
    event_name = event.event
    if event_name == "ChannelOpened":
        participants = (event.args.participant1, event.args.participant2)
        channel_identifier = event.args.channel_identifier
        channel, _ = token_network.channels.get_or_create(
            identifier=channel_identifier, participant_addresses=participants
        )
        return channel

    if event_name == "ChannelClosed":
        channel_identifier = event.args.channel_identifier
        return token_network.channels.filter(identifier=channel_identifier).first()

    return None


def process_events(w3: Web3, token_network: models.TokenNetwork, event_filter):
    try:
        for event in event_filter.get_all_entries():
            logger.info(f"Processing event {event.event} at {event.transactionHash.hex()}")

            block = get_block_by_hash(w3, event.blockHash)
            tx = get_transaction_by_hash(w3, event.transactionHash, block)
            if not tx:
                logger.warning(f"Transaction {event.transactionHash} could not be synced")

            channel = _get_channel_from_event(token_network, event)
            if channel:
                token_network.events.get_or_create(
                    channel=channel, transaction=tx, name=event.event
                )
            else:
                logger.warning(f"Failed to find channel related to event {event}")
    except TimeoutError:
        logger.error(f"Timed-out while getting events for {token_network}")
    except Exception as exc:
        logger.error(f"Failed to get events for {token_network}: {exc}")


@shared_task
def sync_token_network_events():
    w3 = get_web3()
    for token_network in models.TokenNetwork.tracked.all():
        token_network_contract = token_network.get_contract(w3=w3)
        event_blocks = Block.objects.filter(
            transactions__tokennetworkchannelevent__channel__token_network=token_network
        )
        from_block = Block.get_latest_block_number(event_blocks) + 1

        logger.info(f"Fetching {token_network.token} events since block {from_block}")

        channel_open_filter = token_network_contract.events.ChannelOpened.createFilter(
            fromBlock=from_block
        )
        channel_closed_filter = token_network_contract.events.ChannelClosed.createFilter(
            fromBlock=from_block
        )

        process_events(w3=w3, token_network=token_network, event_filter=channel_open_filter)
        process_events(w3=w3, token_network=token_network, event_filter=channel_closed_filter)


@shared_task
def make_udc_deposit(order_id: int):
    order = models.UserDepositContractOrder.objects.filter(id=order_id).first()

    if not order:
        logging.warning(f"UDC Order {order_id} not found")
        return

    w3 = get_web3()
    service_token = get_service_token(w3=w3)
    service_token_amount = EthereumTokenAmount(currency=service_token, amount=order.amount)

    make_service_deposit(w3=w3, raiden=order.raiden, amount=service_token_amount)


@shared_task
def make_channel_deposit(order_id: int):
    order = models.ChannelDepositOrder.objects.filter(id=order_id).first()

    if not order:
        logger.warning(f"Channel Deposit Order {order_id} not found")
        return

    w3 = get_web3()

    client = RaidenClient(order.raiden)
    token_amount = EthereumTokenAmount(currency=order.channel.token, amount=order.amount)

    chain_balance = get_account_balance(
        w3=w3, token=order.channel.token, address=order.raiden.address
    )

    if chain_balance < token_amount:
        logger.warning(f"Insufficient balance {chain_balance.formatted} to deposit on channel")
        return

    client.make_channel_deposit(order.channel, token_amount)


@shared_task
def make_channel_withdraw(order_id: int):
    order = models.ChannelWithdrawOrder.objects.filter(id=order_id).first()

    if not order:
        logger.warning(f"Channel Withdraw Order {order_id} not found")
        return

    client = RaidenClient(order.raiden)
    token_amount = EthereumTokenAmount(currency=order.channel.token, amount=order.amount)
    channel_balance = order.channel.balance_amount

    if channel_balance < token_amount:
        logger.warning(f"Insufficient balance {channel_balance.formatted} to withdraw")
        return

    client.make_channel_withdraw(order.channel, token_amount)


@shared_task
def join_token_network(order_id: int):
    order = models.JoinTokenNetworkOrder.objects.filter(id=order_id).first()

    if not order:
        logger.warning(f"Join Token Network Order {order_id} not found")

    client = RaidenClient(order.raiden)
    token_amount = EthereumTokenAmount(currency=order.token_network.token, amount=order.amount)

    w3 = get_web3()

    chain_balance = get_account_balance(
        w3=w3, token=order.token_network.token, address=order.raiden.address
    )

    if chain_balance < token_amount:
        logger.warning(
            f"Balance {chain_balance.formatted} smaller than request to join token network"
        )
        return

    client.join_token_network(token_network=order.token_network, amount=token_amount)


@shared_task
def leave_token_network(order_id: int):
    order = models.LeaveTokenNetworkOrder.objects.filter(id=order_id).first()

    if not order:
        logger.warning(f"Leave Token Network Order {order_id} not found")
        return

    client = RaidenClient(order.raiden)
    client.leave_token_network(token_network=order.token_network)
