import asyncio
import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from web3 import Web3

from . import signals
from .models import Block, Chain

BLOCK_CREATION_INTERVAL = 10  # In seconds

logger = logging.getLogger(__name__)


@transaction.atomic()
def update_chain_status(w3: Web3):
    chain_id = int(w3.net.version)
    chain = Chain.objects.filter(id=chain_id).first()

    if not chain:
        logger.warning(f"Chain #{chain_id} not created yet")
        return

    syncing = w3.eth.syncing
    client_synced = bool(not syncing)

    if chain.synced and not client_synced:
        signals.ethereum_node_sync_lost.send(sender=Chain, chain=chain)
        chain.refresh_from_db()

    if client_synced and not chain.synced:
        signals.ethereum_node_sync_recovered.send(
            sender=Chain, chain=chain, block_height=w3.eth.blockNumber
        )
        chain.refresh_from_db()

    current_block = w3.eth.blockNumber

    if client_synced and chain.highest_block > current_block:
        signals.chain_reorganization_detected.send(
            sender=Chain, chain=chain, new_block_height=current_block
        )
        chain.refresh_from_db()

    chain.highest_block = current_block
    chain.synced = client_synced
    chain.save()

    sync_status = "synced" if chain.synced else "not synced"
    logger.info(
        f"Client {chain.provider_hostname} is {sync_status}. "
        f"Current block height: {chain.highest_block}"
    )


async def listen_new_blocks(w3: Web3):
    block_filter = w3.eth.filter("latest")
    chain_id = int(w3.net.version)
    while True:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        for event in block_filter.get_new_entries():
            block_hash = event.hex()
            block_data = w3.eth.getBlock(block_hash, full_transactions=True)
            await sync_to_async(signals.block_sealed.send)(
                sender=Block,
                chain_id=chain_id,
                block_data=block_data,
                transactions=block_data.transactions,
            )


async def sync_chain(w3: Web3):
    while True:
        await sync_to_async(update_chain_status)(w3)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
