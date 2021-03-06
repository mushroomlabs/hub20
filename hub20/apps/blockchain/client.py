import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TimeExhausted, TransactionNotFound
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider, IPCProvider, WebsocketProvider
from web3.types import TxParams, Wei

from . import signals
from .app_settings import BLOCK_SCAN_RANGE, DEFAULT_GAS_PRICE_GWEI
from .models import Block, Chain, Transaction

BLOCK_CREATION_INTERVAL = 10  # In seconds
DEFAULT_PRICE = Web3.toWei(DEFAULT_GAS_PRICE_GWEI, "gwei")
WEB3_CLIENTS = {}

logger = logging.getLogger(__name__)


def database_history_gas_price_strategy(w3: Web3, params: TxParams = None) -> Wei:

    BLOCK_HISTORY_SIZE = 100
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber

    txs = Transaction.objects.filter(
        block__chain=chain_id, block__number__gte=current_block_number - BLOCK_HISTORY_SIZE
    )
    return Wei(txs.aggregate(avg_price=Avg("gas_price")).get("avg_price")) or DEFAULT_PRICE


def send_transaction(
    w3: Web3, contract_function, account_address, account_private_key, gas, *args, **kw
):
    transaction_params = {
        "chainId": int(w3.net.version),
        "nonce": w3.eth.getTransactionCount(account_address),
        "gasPrice": kw.pop("gas_price", DEFAULT_PRICE),
        "gas": gas,
    }

    transaction_params.update(**kw)

    result = contract_function(*args)
    transaction_data = result.buildTransaction(transaction_params)
    signed = w3.eth.account.signTransaction(transaction_data, account_private_key)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    return w3.eth.waitForTransactionReceipt(tx_hash)


def make_web3(provider_url: str) -> Web3:
    endpoint = urlparse(provider_url)
    logger.info(f"Instantiating new Web3 for {endpoint.hostname}")
    provider_class = {
        "http": HTTPProvider,
        "https": HTTPProvider,
        "ws": WebsocketProvider,
        "wss": WebsocketProvider,
    }.get(endpoint.scheme, IPCProvider)

    w3 = Web3(provider_class(provider_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.setGasPriceStrategy(database_history_gas_price_strategy)

    return w3


def get_web3(provider_url: Optional[str] = None, force_new: bool = False) -> Web3:
    provider_url = provider_url or settings.WEB3_PROVIDER_URI
    w3 = WEB3_CLIENTS.get(provider_url)

    if w3 is None or force_new:
        w3 = make_web3(provider_url)
        WEB3_CLIENTS[provider_url] = w3

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
        return Transaction.make(
            tx_data=w3.eth.getTransaction(transaction_hash),
            tx_receipt=w3.eth.getTransactionReceipt(transaction_hash),
            block=block,
        )
    except TransactionNotFound:
        return None


def get_block_by_number(w3: Web3, block_number: int) -> Optional[Block]:
    chain_id = int(w3.net.version)
    try:
        block_data = w3.eth.getBlock(block_number, full_transactions=True)
    except AttributeError:
        return None

    logger.info(f"Making block #{block_number} with {len(block_data.transactions)} transactions")
    with transaction.atomic():
        block = Block.make(block_data, chain_id=chain_id)
        for tx_data in block_data.transactions:
            try:
                tx_hash = tx_data.hash.hex()
                Transaction.make(
                    tx_data=tx_data,
                    tx_receipt=w3.eth.waitForTransactionReceipt(tx_hash),
                    block=block,
                )
            except TimeExhausted:
                logger.warning(f"Timeout when trying to get transaction {tx_hash}")
        return block


def run_backfill(w3: Web3, start: int, end: int):
    chain_id = int(w3.net.version)
    block_range = (start, end)
    chain_blocks = Block.objects.filter(chain_id=chain_id, number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        get_block_by_number(w3=w3, block_number=block_number)


async def download_all_chain(w3: Web3):
    start = 0
    highest = w3.eth.blockNumber
    while start < highest:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        end = min(start + BLOCK_SCAN_RANGE, highest)
        logger.info(f"Syncing blocks between {start} and {end}")
        await sync_to_async(run_backfill)(w3=w3, start=start, end=end)
        start = end


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
