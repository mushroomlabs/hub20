import asyncio
import logging
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TimeExhausted, TransactionNotFound
from web3.gas_strategies.time_based import fast_gas_price_strategy
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider, IPCProvider, WebsocketProvider
from web3.types import TxParams, TxReceipt, Wei

from . import signals
from .app_settings import BLOCK_SCAN_RANGE
from .exceptions import Web3TransactionError
from .models import Block, Chain, Transaction

BLOCK_CREATION_INTERVAL = 10  # In seconds
WEB3_CLIENTS: Dict[str, Web3] = {}

logger = logging.getLogger(__name__)


def database_history_gas_price_strategy(w3: Web3, params: Optional[TxParams] = None) -> Wei:

    BLOCK_HISTORY_SIZE = 1000
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber

    txs = Transaction.objects.filter(
        block__chain=chain_id,
        block__number__gte=current_block_number - BLOCK_HISTORY_SIZE,
    )
    avg_price = txs.aggregate(avg_price=Avg("gas_price")).get("avg_price")
    if avg_price:
        wei_price = int(avg_price)
        logger.debug(f"Average Gas Price in last {txs.count()} transactions: {wei_price} wei")
        return Wei(wei_price)
    else:
        logger.debug("No transactions to determine gas price. Default to 'fast' strategy")
        return fast_gas_price_strategy(web3=w3, transaction_params=params)


def send_transaction(
    w3: Web3,
    contract_function,
    account,
    gas,
    contract_args: Optional[Tuple] = None,
    **kw,
) -> TxReceipt:
    nonce = kw.pop("nonce", w3.eth.getTransactionCount(account.address))

    transaction_params = {
        "chainId": int(w3.net.version),
        "nonce": nonce,
        "gasPrice": kw.pop("gas_price", w3.eth.generateGasPrice()),
        "gas": gas,
    }

    transaction_params.update(**kw)

    try:
        result = contract_function(*contract_args) if contract_args else contract_function()
        transaction_data = result.buildTransaction(transaction_params)
        signed = w3.eth.account.signTransaction(transaction_data, account.private_key)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        return w3.eth.waitForTransactionReceipt(tx_hash)
    except ValueError as exc:
        try:
            if exc.args[0].get("message") == "nonce too low":
                logger.warning("Node reported that nonce is too low. Trying tx again...")
                kw["nonce"] = nonce + 1
                return send_transaction(
                    w3,
                    contract_function,
                    account,
                    gas,
                    contract_args=contract_args,
                    **kw,
                )
        except (AttributeError, IndexError):
            pass

        raise Web3TransactionError from exc


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

    wait_for_connection(w3)
    client_network_id = int(w3.net.version)
    app_network_id = settings.BLOCKCHAIN_NETWORK_ID
    if client_network_id != app_network_id:
        raise ValueError(f"Web3 node connected to {client_network_id}, we are on {app_network_id}")

    return w3


def get_block_by_hash(w3: Web3, block_hash: HexBytes) -> Optional[Block]:
    try:
        chain = Chain.objects.get(id=int(w3.net.version))
        block_data = w3.eth.getBlock(block_hash)
        return Block.make(block_data, chain.id)
    except (AttributeError, Chain.DoesNotExist):
        return None


def get_transaction_by_hash(
    w3: Web3, transaction_hash: HexBytes, block: Optional[Block] = None
) -> Optional[Transaction]:
    try:
        tx_data = w3.eth.getTransaction(transaction_hash)

        if block is None:
            block = get_block_by_hash(w3=w3, block_hash=tx_data.blockHash)

        assert block is not None

        return Transaction.make(
            tx_data=tx_data,
            tx_receipt=w3.eth.getTransactionReceipt(transaction_hash),
            block=block,
        )
    except (TransactionNotFound, AssertionError):
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


def fetch_new_block_entries(w3: Web3, block_filter):
    wait_for_connection(w3)
    logger.info("Checking for new blocks...")
    for event in block_filter.get_new_entries():
        block_hash = event.hex()
        logger.info(f"New block: {block_hash}")
        block_data = w3.eth.getBlock(block_hash, full_transactions=True)
        signals.block_sealed.send(sender=Block, block_data=block_data)


def run_backfill(w3: Web3, start: int, end: int):
    chain_id = int(w3.net.version)
    block_range = (start, end)
    chain_blocks = Block.objects.filter(chain_id=chain_id, number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        get_block_by_number(w3=w3, block_number=block_number)


def is_connected_to_blockchain(w3: Web3):
    return w3.isConnected() and (w3.net.peer_count > 0)


def run_ethereum_node_connection_check(w3: Web3):
    chain = Chain.make(chain_id=int(w3.net.version))
    is_connected = is_connected_to_blockchain(w3=w3)

    if is_connected and not chain.online:
        signals.ethereum_node_connected.send(sender=Chain, chain_id=chain.id)
    elif chain.online and not is_connected:
        signals.ethereum_node_disconnected.send(sender=Chain, chain_id=chain.id)
    else:
        logger.debug(f"Ethereum node connected: {is_connected}")

    return is_connected


def wait_for_connection(w3: Web3):
    while not is_connected_to_blockchain(w3=w3):
        logger.info("Not connected to blockchain. Waiting for reconnection...")
        time.sleep(BLOCK_CREATION_INTERVAL / 2)


async def download_all_chain(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    start = 0
    highest = w3.eth.blockNumber
    while start < highest:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        end = min(start + BLOCK_SCAN_RANGE, highest)
        logger.info(f"Syncing blocks between {start} and {end}")
        await sync_to_async(run_backfill)(w3=w3, start=start, end=end)
        start = end


async def listen_new_blocks(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    block_filter = w3.eth.filter("latest")
    while True:
        await sync_to_async(wait_for_connection)(w3)
        await sync_to_async(fetch_new_block_entries)(w3=w3, block_filter=block_filter)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)


async def sync_chain(w3: Web3):
    while True:
        await sync_to_async(wait_for_connection)(w3)
        has_peers = w3.net.peer_count > 0
        is_synced = bool(not w3.eth.syncing)
        await sync_to_async(signals.chain_status_synced.send)(
            sender=Chain,
            chain_id=int(w3.net.version),
            current_block=w3.eth.blockNumber,
            synced=is_synced and has_peers,
        )
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)


async def run_heartbeat(w3: Web3):
    while True:
        await sync_to_async(run_ethereum_node_connection_check)(w3=w3)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
