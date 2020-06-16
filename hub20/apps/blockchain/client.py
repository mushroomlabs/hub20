import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.db.models import Avg
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TransactionNotFound
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


def get_block_by_hash(w3: Web3, block_hash: HexBytes) -> Optional[Block]:
    try:
        chain = Chain.objects.get(id=int(w3.net.version))
        block_data = w3.eth.getBlock(block_hash)
        return Block.make(block_data, chain)
    except (AttributeError, Chain.DoesNotExist):
        return None


def get_transaction_by_hash(
    w3: Web3, transaction_hash: HexBytes, block: Block
) -> Optional[Transaction]:
    try:
        tx_data = w3.eth.getTransaction(transaction_hash)
        assert block.hash == tx_data.blockHash, "Block hash data differ"
        return Transaction.make(tx_data, block)
    except TransactionNotFound:
        return None


async def listen_new_blocks(w3: Web3):
    block_filter = w3.eth.filter("latest")
    while True:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        for event in block_filter.get_new_entries():
            block_hash = event.hex()
            block_data = w3.eth.getBlock(block_hash, full_transactions=True)
            block = await sync_to_async(get_block_by_hash)(w3, block_hash)

            for tx_hash in block_data.transactions:
                await sync_to_async(get_transaction_by_hash)(w3, tx_hash, block)
            await sync_to_async(signals.block_sealed.send)(sender=Block, block=block)


async def sync_chain(w3: Web3):
    while True:
        await sync_to_async(signals.chain_status_synced.send)(
            sender=Chain,
            chain_id=int(w3.net.version),
            current_block=w3.eth.blockNumber,
            synced=bool(not w3.eth.syncing),
        )
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
