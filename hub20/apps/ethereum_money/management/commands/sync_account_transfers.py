import logging
import time

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumToken

POLLING_PERIOD = 10
logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


class Command(BaseCommand):
    help = "Continuously checks for transactions involving accounts we control, syncs to database"

    def handle(self, *args, **options):
        chain = Chain.make()
        w3 = chain.get_web3()

        token_filters = {}

        while True:
            while not w3.isConnected():
                logger.critical("ETH node is disconnected")
                time.sleep(POLLING_PERIOD)
                w3 = chain.make(force_new=True)

            tokens = EthereumToken.ERC20tokens.filter(chain=chain)
            accounts = EthereumAccount.objects.values_list("address", flat=True)

            for token in tokens:
                if token.address not in token_filters:
                    logger.info(f"Will start tracking token {token}")
                    token_filters[token.address] = token.get_web3_filter(w3)

                token_filter = token_filters[token.address]
                logger.info(f"Checking events for token {token.address}")
                for tx_hash in token_filter.get_new_entries():
                    tx = w3.eth.waitForTransactionReceipt(tx_hash)
                    contract = token.get_contract(w3)
                    recipient, _ = token._decode_transaction_data(tx, contract)

                    if recipient in accounts:
                        Transaction.fetch_by_hash(tx_hash)

            time.sleep(POLLING_PERIOD / 2)
