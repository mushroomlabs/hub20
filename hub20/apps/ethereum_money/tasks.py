import logging
from concurrent.futures import TimeoutError
from typing import List

from celery import shared_task
from web3.exceptions import TransactionNotFound

from hub20.apps.blockchain.models import Chain
from hub20.apps.ethereum_money.models import EthereumToken

from .signals import blockchain_payment_sent

logger = logging.getLogger(__name__)


@shared_task
def check_transaction_for_erc20_transfer(tx_hash: str, account_addresses: List[str]):
    chain = Chain.make()
    w3 = chain.get_web3()

    try:
        tx = w3.eth.getTransaction(tx_hash)
        token_address = tx["to"]
        token = EthereumToken.objects.filter(chain=chain, address=token_address).first()
        if token:
            logger.info(f"Processing {token.code} transaction: {tx_hash}")
            contract = token.get_contract(w3)

            recipient, value = token._decode_transaction_data(tx, contract)
            valid_transaction = all(
                [recipient is not None, value is not None, recipient in account_addresses]
            )

            if valid_transaction:
                blockchain_payment_sent.send(
                    sender=EthereumToken,
                    recipient=recipient,
                    amount=value,
                    transaction_hash=tx_hash,
                )
    except TimeoutError:
        logger.error(f"Failed request to get or check {tx_hash}")
    except TransactionNotFound:
        logger.info(f"Tx {tx_hash} has not yet been mined")
    except ValueError as exc:
        logger.error(str(exc))
    except Exception as exc:
        logger.exception(exc)


@shared_task
def check_transaction_for_eth_transfer(tx_hash: str, account_addresses: List[str]):
    chain = Chain.make()
    w3 = chain.get_web3()

    try:
        tx = w3.eth.getTransaction(tx_hash)

        if tx.to in account_addresses:
            ETH = EthereumToken.ETH(chain)
            blockchain_payment_sent.send(
                sender=EthereumToken,
                recipient=tx.to,
                amount=ETH.from_wei(tx.value),
                transaction_hash=tx_hash,
            )

    except TimeoutError:
        logger.warn(f"Failed request to get {tx_hash}")
    except TransactionNotFound:
        logger.info(f"Tx {tx_hash} has not yet been mined")
    except ValueError as exc:
        logger.error(str(exc))
    except Exception as exc:
        logger.exception(exc)
