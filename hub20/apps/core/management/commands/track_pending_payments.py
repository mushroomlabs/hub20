import logging
import time
from concurrent.futures import TimeoutError

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.models import Transaction, make_web3
from hub20.apps.core import tasks
from hub20.apps.core.models import Wallet
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)
SLEEP_INTERVAL = 3


def track_pending_transactions(w3):
    chain_id = int(w3.net.version)

    tx_filter = w3.eth.filter("pending")

    while True:
        time.sleep(SLEEP_INTERVAL)
        wallets = Wallet.objects.filter(paymentordermethod__isnull=False)
        tokens = EthereumToken.ERC20tokens.filter(
            chain=chain_id, paymentorder__payment_method__isnull=False
        )

        # Convert the querysets to lists of addresses
        wallet_addresses = wallets.values_list("account__address", flat=True)[::1]
        token_addresses = tokens.values_list("address", flat=True)[::1]

        if not wallet_addresses:
            logger.info("No open payment order...")
            continue

        try:
            pending_entries = [entry.hex() for entry in tx_filter.get_new_entries()]
            recorded_tx_hashes = Transaction.objects.filter(hash__in=pending_entries).values_list(
                "hash", flat=True
            )[::1]
            for tx_hash in set(pending_entries) - set(recorded_tx_hashes):
                address_list = ", ".join([str(a) for a in wallet_addresses])
                logger.info(f"Checking {tx_hash} for blockchain transfers at {address_list}")
                tasks.check_transaction_for_eth_transfer.delay(tx_hash, wallet_addresses)

                if token_addresses:
                    tasks.check_transaction_for_erc20_transfer.delay(
                        tx_hash, wallet_addresses, token_addresses
                    )
        except TimeoutError:
            logger.warn("Timeout error when getting new entries")


class Command(BaseCommand):
    help = "Listens to pending transactions looking for payments sent via blockchain"

    def handle(self, *args, **options):
        w3 = make_web3()
        track_pending_transactions(w3)
