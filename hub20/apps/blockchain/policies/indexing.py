import logging
import time

from ..models import Chain
from ..signals import (
    ethereum_node_connected,
    ethereum_node_disconnected,
    ethereum_node_sync_lost,
    ethereum_node_sync_recovered,
)
from ..tasks import fetch_block

logger = logging.getLogger(__name__)

BLOCK_RANGE = 5000
TASK_PRIORITY = 9
WAITING_INTERVAL = 10


def _run_fetch(block_number, background=False):
    if background:
        logger.info(f"Scheduling fetch of block {block_number}")
        fetch_block.apply_async(args=(block_number,), priority=TASK_PRIORITY)
    else:
        logger.info(f"Fetching block {block_number}")
        fetch_block(block_number)


def make_blocks_in_range(chain: Chain, start: int, end: int, background: bool = False):
    block_range = (start, end)
    chain_blocks = chain.blocks.filter(number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        _run_fetch(block_number, background=background)


def index(chain, start_point, stop_point, background=False):
    lower_bound = start_point
    while lower_bound < stop_point:
        upper_bound = min(lower_bound + BLOCK_RANGE, stop_point)
        logger.debug(f"Backfilling missing blocks between {lower_bound} and {upper_bound}")
        make_blocks_in_range(chain, lower_bound, upper_bound, background=background)
        lower_bound = upper_bound

    _run_fetch(stop_point, background=background)


def _ensure_connected(chain):
    w3 = chain.get_web3()

    connection_lost = False

    while not w3.isConnected():
        connection_lost = True
        ethereum_node_disconnected(sender=Chain, chain=chain)
        logger.critical("ETH node is disconnected")
        time.sleep(WAITING_INTERVAL)
        w3 = chain.get_web3(force_new=True)

    if connection_lost:
        ethereum_node_connected(sender=Chain, chain=chain)
    return w3


def _ensure_synced(chain):
    w3 = chain.get_web3()

    out_of_sync = False

    while syncing := w3.eth.syncing:
        logger.critical(
            f"ETH node is syncing: {syncing['currentBlock']}/{syncing['highestBlock']}"
        )
        out_of_sync = True
        ethereum_node_sync_lost.send(sender=Chain, chain=chain)
        time.sleep(WAITING_INTERVAL)

    if out_of_sync:
        ethereum_node_sync_recovered(sender=Chain, chain=chain)


def _run_backfill_policy(starting_block=0, background=False):
    chain = Chain.make()
    w3 = _ensure_connected(chain)

    current_block = 0
    while current_block < w3.eth.blockNumber:
        start, end = current_block, current_block + BLOCK_RANGE
        logger.info(f"Running backfill between {start} and {end}")
        index(chain, start, end, background=background)
        current_block = end
        w3 = _ensure_connected(chain)


class BackfillWeb3Indexer:
    def __call__(self):
        _run_backfill_policy()


class BackfillCeleryWeb3Indexer:
    def __call__(self):
        _run_backfill_policy(background=True)


class FullArchiveStreamingWeb3Indexer:
    def __call__(self):
        chain = Chain.make()

        while True:
            chain.refresh_from_db()
            w3 = _ensure_connected(chain)

            _ensure_synced(chain)

            current = w3.eth.blockNumber

            highest_block = chain.highest_block

            if current < highest_block:
                logger.warning(f"ETH node block is {current} and we have {highest_block}")
                time.sleep(WAITING_INTERVAL * 2)
            elif current == highest_block:
                logger.info(f"In sync. Sleeping {WAITING_INTERVAL} seconds")
                time.sleep(WAITING_INTERVAL)
            elif current == (highest_block - 1):
                _run_fetch(current)
            else:
                index(chain, highest_block, current)


class ChainStatusWeb3Indexer:
    def __call__(self):
        chain = Chain.make()

        while True:
            chain.refresh_from_db()
            w3 = _ensure_connected(chain)

            _ensure_synced(chain)

            chain.highest_block = w3.eth.blockNumber
            chain.synced = True
            chain.save()

            time.sleep(WAITING_INTERVAL)


__all__ = [
    "BackfillWeb3Indexer",
    "BackfillCeleryWeb3Indexer",
    "FullArchiveStreamingWeb3Indexer",
    "ChainStatusWeb3Indexer",
]
