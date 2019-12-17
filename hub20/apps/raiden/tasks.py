import logging
from concurrent.futures import TimeoutError
from typing import Optional

from celery import shared_task
from hub20.apps.blockchain.models import make_web3, Block, Transaction

from .models import TokenNetwork, TokenNetworkChannel

logger = logging.getLogger(__name__)


def _get_channel_from_event(token_network, event) -> Optional[TokenNetworkChannel]:
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


def process_events(token_network, event_filter, w3):
    try:
        for event in event_filter.get_all_entries():
            logger.info(f"Processing event {event.event} at {event.transactionHash.hex()}")
            tx = Transaction.fetch_by_hash(event.transactionHash, w3=w3)
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
    w3 = make_web3()
    for token_network in TokenNetwork.objects.all():
        token_network_contract = token_network.get_contract(w3=w3)
        event_blocks = Block.objects.filter(
            transaction__tokennetworkchannelevent__channel__token_network=token_network
        )
        from_block = Block.get_latest_block_number(event_blocks) + 1

        logger.info(f"Fetching {token_network.token} events since block {from_block}")

        channel_open_filter = token_network_contract.events.ChannelOpened.createFilter(
            fromBlock=from_block
        )
        channel_closed_filter = token_network_contract.events.ChannelClosed.createFilter(
            fromBlock=from_block
        )

        process_events(token_network, channel_open_filter, w3)
        process_events(token_network, channel_closed_filter, w3)
