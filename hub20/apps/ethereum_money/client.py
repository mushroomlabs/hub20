import asyncio
import logging
from typing import Dict

from asgiref.sync import sync_to_async
from ethtoken.abi import EIP20_ABI
from web3 import Web3
from web3.exceptions import TransactionNotFound

from hub20.apps.blockchain.client import BLOCK_CREATION_INTERVAL
from hub20.apps.blockchain.models import Block, Chain, Transaction
from hub20.apps.ethereum_money import get_ethereum_account_model, signals
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


def process_transaction_data(
    w3: Web3,
    block_data,
    tx_data,
    sender_address,
    recipient_address,
    accounts_by_address: Dict[str, EthereumAccount],
):
    sender = accounts_by_address.get(sender_address)
    recipient = accounts_by_address.get(recipient_address)

    if sender is None and recipient is None:
        return

    chain_id = int(w3.net.version)
    chain = Chain.make(chain_id=chain_id)
    block = Block.make(block_data, chain=chain)

    tx = Transaction.make(tx_data, block=block)

    if sender:
        signals.outgoing_transfer_mined.send(sender=Transaction, account=sender, transaction=tx)

    if recipient:
        signals.incoming_transfer_mined.send(sender=Transaction, account=recipient, transaction=tx)


def get_erc20_transfer_recipient(w3: Web3, token: EthereumToken, tx_receipt):
    contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
    tx_logs = contract.events.Transfer().processReceipt(tx_receipt)
    assert len(tx_logs) == 1, "There should be only one log entry on transfer function"

    return tx_logs[0].args._to


async def listen_transfers(w3: Web3):
    block_filter = w3.eth.filter("latest")
    chain_id = int(w3.net.version)

    while True:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL / 2)
        accounts_by_addresses = await sync_to_async(
            lambda: {a.address: a for a in EthereumAccount.objects.all()}
        )()
        token_qs = EthereumToken.ERC20tokens.filter(chain_id=chain_id).select_related("chain")
        tokens = await sync_to_async(tuple)(token_qs)
        tokens_by_address = {token.address: token for token in tokens}

        for block_hash in block_filter.get_new_entries():
            block_data = w3.eth.getBlock(block_hash.hex(), full_transactions=True)

            logger.info(f"Checking block {block_hash.hex()} for relevant transfers")
            for tx_data in block_data.transactions:
                tx_hash = tx_data.hash
                logger.info(f"Checking Tx {tx_hash.hex()}")
                sender = tx_data["from"]

                token = tokens_by_address.get(tx_data.to)
                if token:
                    # Possible ERC20 token transfer
                    try:
                        tx_receipt = w3.eth.getTransactionReceipt(tx_data.hash)
                        recipient = get_erc20_transfer_recipient(w3, token, tx_receipt)
                    except TransactionNotFound:
                        logger.warning(f"Could not get tx {tx_hash.hex()}")
                        recipient = None
                    except AssertionError as exc:
                        logger.warning(exc)
                        recipient = None
                    except Exception as exc:
                        logger.exception(exc)
                        recipient = None
                else:
                    recipient = tx_data.to

                process_transaction_data(
                    w3=w3,
                    block_data=block_data,
                    tx_data=tx_data,
                    sender_address=sender,
                    recipient_address=recipient,
                    accounts_by_address=accounts_by_addresses,
                )
