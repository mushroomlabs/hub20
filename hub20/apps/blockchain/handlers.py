import logging

from django.db import transaction
from django.dispatch import receiver

from . import signals
from .models import Chain

logger = logging.getLogger(__name__)


@receiver(signals.chain_status_synced, sender=Chain)
def on_chain_status_synced_update_database(sender, **kw):
    try:
        chain_id = int(kw["chain_id"])
        current_block = int(kw["current_block"])
        synced: bool = kw["synced"]
    except Exception as exc:
        logger.exception(exc)
        return

    chain = Chain.objects.filter(id=chain_id).first()

    if not chain:
        logger.warning(f"Chain #{chain_id} not created yet")
        return

    with transaction.atomic():
        if chain.synced and not synced:
            signals.ethereum_node_sync_lost.send(sender=Chain, chain=chain)
            chain.refresh_from_db()

        if synced and not chain.synced:
            signals.ethereum_node_sync_recovered.send(
                sender=Chain, chain=chain, block_height=current_block
            )
            chain.refresh_from_db()

            if synced and chain.highest_block > current_block:
                signals.chain_reorganization_detected.send(
                    sender=Chain, chain=chain, new_block_height=current_block
                )
            chain.refresh_from_db()

        chain.highest_block = current_block
        chain.synced = synced
        chain.save()

    sync_status = "synced" if chain.synced else "not synced"
    logger.info(
        f"Client {chain.provider_hostname} is {sync_status}. "
        f"Current block height: {chain.highest_block}"
    )


@receiver(signals.chain_reorganization_detected, sender=Chain)
def on_chain_reorganization_clear_blocks(sender, **kw):
    chain = kw["chain"]
    block_number = kw["new_block_height"]

    logger.warning(f"Re-org detected. Rewinding to block #{block_number}")
    chain.blocks.filter(number__gt=block_number).delete()


@receiver(signals.ethereum_node_sync_lost, sender=Chain)
def on_sync_lost_update_chain(sender, **kw):
    chain = kw["chain"]
    logger.warning(f"Client {chain.provider_url} lost sync")
    chain.synced = False
    chain.save()


@receiver(signals.ethereum_node_sync_recovered, sender=Chain)
def on_sync_recovered_update_chain(sender, **kw):
    chain = kw["chain"]
    logger.warning(f"Client {chain.provider_hostname} back in sync")
    chain.synced = True
    chain.highest_block = kw["block_height"]
    chain.save()


__all__ = [
    "on_sync_lost_update_chain",
    "on_sync_recovered_update_chain",
    "on_chain_status_synced_update_database",
    "on_chain_reorganization_clear_blocks",
]
