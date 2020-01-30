import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from eth_utils import from_wei

from hub20.apps.blockchain.models import Transaction, TransactionLog
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.ethereum_money.signals import account_deposit_received

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


@receiver(post_save, sender=Transaction)
def on_transaction_mined_check_for_deposit(sender, **kw):
    tx = kw["instance"]
    if kw["created"]:
        accounts = EthereumAccount.objects.all()
        accounts_by_address = {account.address: account for account in accounts}

        if tx.to_address in accounts_by_address.keys():
            ETH = EthereumToken.ETH(tx.block.chain)
            eth_amount = EthereumTokenAmount(amount=from_wei(tx.value, "ether"), currency=ETH)
            account_deposit_received.send(
                sender=Transaction,
                account=accounts_by_address[tx.to_address],
                transaction=tx,
                amount=eth_amount,
            )


@receiver(post_save, sender=TransactionLog)
def on_transaction_event_check_for_token_transfer(sender, **kw):
    tx_log = kw["instance"]

    logger.info(f"Event log for {tx_log.transaction} created")
    if kw["created"]:
        tx = tx_log.transaction
        token = EthereumToken.ERC20tokens.filter(address=tx.to_address).first()

        if token is not None:
            recipient_address, transfer_amount = token._decode_token_transfer_input(tx)
            is_token_transfer = recipient_address is not None and transfer_amount is not None

            account = EthereumAccount.objects.filter(address=recipient_address).first()
            if is_token_transfer and account:
                account_deposit_received.send(
                    sender=Transaction, account=account, transaction=tx, amount=transfer_amount
                )


@receiver(account_deposit_received, sender=Transaction)
def on_account_deposit_create_balance_entry(sender, **kw):
    account = kw["account"]
    transaction = kw["transaction"]
    amount = kw["amount"]

    try:
        account.balance_entries.create(
            amount=amount.amount, currency=amount.currency, transaction=transaction
        )
    except Exception as exc:
        logger.exception(exc)


__all__ = [
    "on_transaction_mined_check_for_deposit",
    "on_transaction_event_check_for_token_transfer",
    "on_account_deposit_create_balance_entry",
]
