import logging
import time

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.blockchain.policies.indexing import WAITING_INTERVAL, _ensure_connected
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


class AccountTransferStreamingWeb3Indexer:
    def __call__(self):
        chain = Chain.make()
        w3 = chain.get_web3()

        tx_filter = w3.eth.filter("latest")

        while True:
            chain.refresh_from_db()
            w3 = _ensure_connected(chain)

            # Small dance with the web3 object from the filter in case a new
            # was generated due to re-connection
            tx_filter.web3 = w3

            accounts = EthereumAccount.objects.values_list("address", flat=True)

            for tx_hash in tx_filter.get_new_entries():
                logger.info(f"Checking ETH transfers on {tx_hash.hex()}")
                tx = w3.eth.waitForTransactionReceipt(tx_hash)
                if tx["from"] in accounts or tx.to in accounts:
                    Transaction.fetch_by_hash(tx_hash)

            time.sleep(WAITING_INTERVAL)


class Erc20TokenTransferStreamingWeb3Indexer:
    def __call__(self):
        chain = Chain.make()
        token_filters = {}

        while True:
            chain.refresh_from_db()
            w3 = _ensure_connected(chain)

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

                    if recipient in accounts or tx.to in accounts:
                        Transaction.fetch_by_hash(tx_hash)

            time.sleep(WAITING_INTERVAL)


__all__ = [
    "AccountTransferStreamingWeb3Indexer",
    "Erc20TokenTransferStreamingWeb3Indexer",
]
