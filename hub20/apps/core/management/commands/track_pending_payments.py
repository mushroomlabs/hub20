import datetime
import logging
import time
from concurrent.futures import TimeoutError

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.core import tasks
from hub20.apps.core.models import PaymentOrder

logger = logging.getLogger(__name__)
BLOCK_INTERVAL = 10


def track_pending_transactions():
    chain = Chain.make()
    w3 = chain.get_web3()

    tx_filter = w3.eth.filter("pending")

    while True:
        chain.refresh_from_db()

        if not chain.synced:
            logger.info("Chain not synced. Sleeping...")
            time.sleep(BLOCK_INTERVAL)
            continue

        open_orders = PaymentOrder.objects.unpaid().with_blockchain_route()

        if not open_orders:
            logger.info("No open payment order...")
            time.sleep(BLOCK_INTERVAL / 2)
            continue

        logger.info(f"Looking for pending transactions from {chain.highest_block}")
        # Convert the querysets to lists of addresses
        account_addresses = open_orders.values_list(
            "routes__blockchainpaymentroute__account__address", flat=True
        ).distinct()[::1]

        try:
            expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=BLOCK_INTERVAL)
            prio = 0
            pending_entries = [entry.hex() for entry in tx_filter.get_new_entries()]
            recorded_tx_hashes = Transaction.objects.filter(hash__in=pending_entries).values_list(
                "hash", flat=True
            )[::1]
            for tx_hash in set(pending_entries) - set(recorded_tx_hashes):
                address_list = ", ".join([str(a) for a in account_addresses])

                logger.info(f"Checking {tx_hash} for blockchain transfers at {address_list}")
                tasks.check_transaction_for_eth_transfer.apply_async(
                    args=(tx_hash, account_addresses), expires=expiration_time, priority=prio
                )
                tasks.check_transaction_for_erc20_transfer.apply_async(
                    args=(tx_hash, account_addresses), expires=expiration_time, priority=prio,
                )
        except TimeoutError:
            logger.warn("Timeout error when getting new entries")

        time.sleep(BLOCK_INTERVAL / 2)


class Command(BaseCommand):
    help = "Listens to pending transactions looking for payments sent via blockchain"

    def handle(self, *args, **options):
        track_pending_transactions()
