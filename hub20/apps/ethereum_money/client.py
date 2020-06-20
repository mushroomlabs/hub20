import asyncio
import logging
from typing import Optional

from asgiref.sync import sync_to_async
from ethtoken.abi import EIP20_ABI
from web3 import Web3
from web3.exceptions import TransactionNotFound

from hub20.apps.blockchain.client import BLOCK_CREATION_INTERVAL
from hub20.apps.blockchain.models import Block, Chain, Transaction
from hub20.apps.ethereum_money import get_ethereum_account_model, signals
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


def _decode_transfer_arguments(w3: Web3, token: EthereumToken, tx_data):
    contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)

    fn, args = contract.decode_function_input(tx_data.input)

    # TODO: is this really the best way to identify the transaction as a value transfer?
    transfer_idenfifier = contract.functions.transfer.function_identifier
    if not transfer_idenfifier == fn.function_identifier:
        return None

    return args


def get_transfer_value_by_tx_data(
    w3: Web3, token: EthereumToken, tx_data
) -> Optional[EthereumTokenAmount]:
    args = _decode_transfer_arguments(w3, token, tx_data)
    if args is not None:
        return token.from_wei(args._value)


def get_transfer_recipient_by_tx_data(w3: Web3, token: EthereumToken, tx_data):
    args = _decode_transfer_arguments(w3, token, tx_data)
    if args is not None:
        return args._to


def get_transfer_recipient_by_receipt(w3: Web3, token: EthereumToken, tx_receipt):
    contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
    tx_logs = contract.events.Transfer().processReceipt(tx_receipt)
    assert len(tx_logs) == 1, "There should be only one log entry on transfer function"

    return tx_logs[0].args._to


def process_pending_transfers(w3: Web3, chain: Chain, tx_filter):
    chain.refresh_from_db()

    # Convert the querysets to lists of addresses
    accounts_by_addresses = EthereumAccount.objects.values_list("address", flat=True)
    tokens_by_address = {
        token.address: token for token in EthereumToken.ERC20tokens.filter(chain=chain)
    }
    ETH = EthereumToken.ETH(chain=chain)

    pending_txs = [entry.hex() for entry in tx_filter.get_new_entries()]
    recorded_txs = tuple(
        Transaction.objects.filter(hash__in=pending_txs).values_list("hash", flat=True)
    )
    for tx_hash in set(pending_txs) - set(recorded_txs):
        logger.info(f"Processing pending Tx {tx_hash}")
        try:
            tx_data = w3.eth.getTransaction(tx_hash)
            token = tokens_by_address.get(tx_data.to)
            if token:
                recipient_address = get_transfer_recipient_by_tx_data(w3, token, tx_data)
                amount = get_transfer_value_by_tx_data(w3, token, tx_data)
            elif tx_data.to in accounts_by_addresses:
                recipient_address = tx_data.to
                amount = ETH.from_wei(tx_data.value)
            else:
                continue

            recipient = accounts_by_addresses.get(recipient_address)
            if recipient is not None and amount is not None:
                signals.incoming_transfer_broadcast.send(
                    sender=EthereumToken,
                    account=recipient,
                    amount=amount,
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


def process_latest_transfers(w3: Web3, chain: Chain, block_filter):
    chain.refresh_from_db()

    accounts_by_address = {a.address: a for a in EthereumAccount.objects.all()}
    tokens = EthereumToken.ERC20tokens.filter(chain=chain).select_related("chain")
    tokens_by_address = {token.address: token for token in tokens}

    for block_hash in block_filter.get_new_entries():
        block_data = w3.eth.getBlock(block_hash.hex(), full_transactions=True)

        logger.info(f"Checking block {block_hash.hex()} for relevant transfers")
        for tx_data in block_data.transactions:
            tx_hash = tx_data.hash
            logger.info(f"Checking Tx {tx_hash.hex()}")
            sender_address = tx_data["from"]

            token = tokens_by_address.get(tx_data.to)
            if token:
                # Possible ERC20 token transfer
                try:
                    tx_receipt = w3.eth.getTransactionReceipt(tx_data.hash)
                    recipient_address = get_transfer_recipient_by_receipt(w3, token, tx_receipt)
                except TransactionNotFound:
                    logger.warning(f"Could not get tx {tx_hash.hex()}")
                    recipient_address = None
                except AssertionError as exc:
                    logger.warning(exc)
                    recipient_address = None
                except Exception as exc:
                    logger.exception(exc)
                    recipient_address = None
            else:
                recipient_address = tx_data.to

            sender_account = accounts_by_address.get(sender_address)
            recipient_account = accounts_by_address.get(recipient_address)

            if sender_account or recipient_account:
                block = Block.make(block_data, chain_id=chain.id)
                Transaction.make(tx_data, block=block)


async def listen_latest_transfers(w3: Web3):
    block_filter = w3.eth.filter("latest")
    chain_id = int(w3.net.version)

    while True:
        chain = await sync_to_async(Chain.make)(chain_id=chain_id)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        await sync_to_async(process_latest_transfers)(w3, chain, block_filter)


async def listen_pending_transfers(w3: Web3):
    tx_filter = w3.eth.filter("pending")
    chain_id = int(w3.net.version)

    while True:
        chain = await sync_to_async(Chain.make)(chain_id=chain_id)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL / 2)
        await sync_to_async(process_pending_transfers)(w3, chain, tx_filter)
