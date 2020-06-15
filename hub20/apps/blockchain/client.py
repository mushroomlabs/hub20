import asyncio
import logging
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.db.models import Avg
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider, IPCProvider, WebsocketProvider
from web3.types import TxParams, Wei

from . import signals
from .models import Block, Chain, Transaction

BLOCK_CREATION_INTERVAL = 10  # In seconds

logger = logging.getLogger(__name__)


def database_history_gas_price_strategy(w3: Web3, params: TxParams = None) -> Wei:

    BLOCK_HISTORY_SIZE = 100
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber
    default_price = Web3.toWei(1.2, "gwei")

    txs = Transaction.objects.filter(
        block__chain=chain_id, block__number__gte=current_block_number - BLOCK_HISTORY_SIZE
    )
    return Wei(txs.aggregate(avg_price=Avg("gas_price")).get("avg_price")) or default_price


def make_web3(chain) -> Web3:
    endpoint = urlparse(chain.provider_url)
    logger.info(f"Instantiating new Web3 for {endpoint.hostname}")
    provider_class = {
        "http": HTTPProvider,
        "https": HTTPProvider,
        "ws": WebsocketProvider,
        "wss": WebsocketProvider,
    }.get(endpoint.scheme, IPCProvider)

    w3 = Web3(provider_class(chain.provider_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.setGasPriceStrategy(database_history_gas_price_strategy)

    chain_id = int(w3.net.version)
    message = f"{endpoint.hostname} connected to {chain_id}, expected {chain.id}"
    assert chain_id == chain.id, message

    return w3


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

        await sync_to_async(signals.chain_status_synced.send)(
            sender=Chain,
            chain_id=int(w3.net.version),
            current_block=w3.eth.blockNumber,
            synced=bool(not w3.eth.syncing),
        )
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
