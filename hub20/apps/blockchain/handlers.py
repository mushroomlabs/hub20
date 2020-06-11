import logging

from django.dispatch import receiver

from . import models, signals

logger = logging.getLogger(__name__)


@receiver(signals.ethereum_node_sync_lost, sender=models.Chain)
def on_sync_lost_update_chain(sender, **kw):
    chain = kw["chain"]
    chain.synced = False
    chain.save()


@receiver(signals.ethereum_node_sync_recovered, sender=models.Chain)
def on_sync_recovered_update_chain(sender, **kw):
    chain = kw["chain"]
    chain.synced = True
    chain.highest_block = kw["block_height"]
    chain.save()


@receiver(signals.blockchain_reorganization_detected, sender=models.Chain)
def on_chain_reorganization_clear_blocks(sender, **kw):
    chain = kw["chain"]
    block_number = kw["block_height"]

    chain.blocks.filter(number__gte=block_number).delete()


__all__ = [
    "on_sync_lost_update_chain",
    "on_sync_recovered_update_chain",
    "on_chain_reorganization_clear_blocks",
]
