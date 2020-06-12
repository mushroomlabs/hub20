import logging

from django.dispatch import receiver

from . import signals, tasks
from .models import Block, Chain

logger = logging.getLogger(__name__)


@receiver(signals.ethereum_node_sync_lost, sender=Chain)
def on_sync_lost_update_chain(sender, **kw):
    chain = kw["chain"]
    logger.warning(f"Client {chain.provider_url} lost sync")
    chain.synced = False
    chain.save()


@receiver(signals.ethereum_node_sync_recovered, sender=Chain)
def on_sync_recovered_update_chain(sender, **kw):
    chain = kw["chain"]
    logger.warning(f"Client {chain.provider_url} back in sync")
    chain.synced = True
    chain.highest_block = kw["block_height"]
    chain.save()


@receiver(signals.chain_reorganization_detected, sender=Chain)
def on_chain_reorganization_clear_blocks(sender, **kw):
    chain = kw["chain"]
    block_number = kw["new_block_height"]

    logger.warning(f"Re-org detected. Rewinding to block #{block_number}")
    chain.blocks.filter(number__gt=block_number).delete()


@receiver(signals.block_sealed, sender=Block)
def on_block_sealed_save_on_database(sender, **kw):
    chain_id = kw["chain_id"]
    block_data = kw["block_data"]
    transactions = kw.get("transactions") or []

    tasks.make_block(chain_id, block_data, transactions)


__all__ = [
    "on_sync_lost_update_chain",
    "on_sync_recovered_update_chain",
    "on_chain_reorganization_clear_blocks",
    "on_block_sealed_save_on_database",
]
