import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.core.models.accounting import (
    BlockchainAccount,
    ExternalAddressAccount,
    RaidenAccount,
    RaidenChannelAccount,
    Treasury,
    UserAccount,
    WalletAccount,
)
from hub20.apps.core.models.payments import PaymentConfirmation
from hub20.apps.core.models.transfers import (
    BlockchainTransferExecution,
    RaidenTransferExecution,
    Transfer,
    TransferCancellation,
    TransferExecution,
    TransferFailure,
)
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.signals import account_deposit_received, outgoing_transfer_mined
from hub20.apps.raiden.models import Channel, Payment as RaidenPayment, Raiden

logger = logging.getLogger(__name__)
User = get_user_model()
EthereumAccount = get_ethereum_account_model()


@receiver(post_save, sender=User)
def on_user_created_create_account(sender, **kw):
    if kw["created"]:
        UserAccount.objects.get_or_create(user=kw["instance"])


@receiver(post_save, sender=Chain)
def on_chain_created_create_account(sender, **kw):
    if kw["created"]:
        BlockchainAccount.objects.get_or_create(chain=kw["instance"])
        Treasury.objects.get_or_create(chain=kw["instance"])


@receiver(post_save, sender=Raiden)
def on_raiden_created_create_account(sender, **kw):
    if kw["created"]:
        RaidenAccount.objects.get_or_create(raiden=kw["instance"])


@receiver(post_save, sender=EthereumAccount)
def on_wallet_created_create_account(sender, **kw):
    if kw["created"]:
        WalletAccount.objects.get_or_create(account=kw["instance"])


@receiver(post_save, sender=Channel)
def on_raiden_channel_created_create_account(sender, **kw):
    if kw["created"]:
        RaidenChannelAccount.objects.get_or_create(channel=kw["instance"])


@receiver(post_save, sender=PaymentConfirmation)
def on_payment_confirmed_record_entries(sender, **kw):
    if kw["created"]:
        confirmation = kw["instance"]
        payment = confirmation.payment

        payee = payment.route.deposit.user
        payee_book = payee.account.get_book(token=payment.currency)

        entry_data = dict(reference=confirmation, amount=payment.amount, currency=payment.currency)

        if hasattr(payment.route, "blockchainpaymentroute"):
            ethereum_account = payment.route.blockchainpaymentroute.account
            wallet_book = ethereum_account.onchain_account.get_book(token=payment.currency)
            wallet_book.debits.create(**entry_data)
            payee_book.credits.create(**entry_data)
        elif hasattr(payment.route, "raidenpaymentroute"):
            raiden = payment.route.raidenpaymentroute.raiden
            raiden_book = raiden.raiden_account.get_book(token=payment.currency)
            raiden_book.debits.create(**entry_data)
            payee_book.credits.create(**entry_data)
        else:
            logger.info(f"Payment {payment} was not routed through any external network")


@receiver(post_save, sender=Transfer)
def on_transfer_created_deduct_sender_balance(sender, **kw):
    if kw["created"]:
        transfer = kw["instance"]
        user_book = transfer.sender.account.get_book(token=transfer.currency)
        user_book.debits.create(
            reference=transfer, currency=transfer.currency, amount=transfer.amount
        )
        treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)
        treasury_book.credits.create(
            reference=transfer, currency=transfer.currency, amount=transfer.amount
        )


@receiver(post_save, sender=TransferExecution)
def on_internal_transfer_executed_move_funds_from_treasury_to_receiver(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        if not transfer.receiver:
            logging.warning("Expected Internal Transfer, but no receiver user defined")
            return

        try:
            treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)
            receiver_book = transfer.receiver.account.get_book(token=transfer.currency)

            params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

            treasury_book.debits.create(**params)
            receiver_book.credits.create(**params)
        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=BlockchainTransferExecution)
def on_blockchain_transfer_executed_move_funds_from_wallet_to_blockchain(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        try:
            params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)
            wallet = EthereumAccount.objects.get(address=execution.transaction.from_address)
            wallet_book = wallet.onchain_account.get_book(token=transfer.currency)
            chain_book = transfer.currency.chain.account.get_book(token=transfer.currency)

            wallet_book.debits.create(**params)
            chain_book.credits.create(**params)

        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=BlockchainTransferExecution)
def on_blockchain_transfer_executed_record_fee_entries(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transaction = execution.transaction

        try:
            chain = transaction.block.chain
            fee = execution.fee
            ETH = execution.fee.currency
            wallet = EthereumAccount.objects.get(address=transaction.from_address)

            treasury_book = chain.treasury.get_book(token=ETH)
            wallet_book = wallet.onchain_account.get_book(token=ETH)
            blockchain_book = chain.account.get_book(token=ETH)
            sender_book = execution.transfer.sender.account.get_book(token=ETH)

            params = dict(reference=execution, currency=ETH, amount=fee.amount)

            # Entry: sender -> treasury
            sender_book.debits.create(**params)
            treasury_book.credits.create(**params)

            # Entry: wallet -> blockchain
            wallet_book.debits.create(**params)
            blockchain_book.credits.create(**params)
        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=RaidenTransferExecution)
def on_raiden_transfer_executed_move_funds_from_account_to_network(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer
        payment = execution.payment
        params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

        try:
            raiden_account_book = payment.channel.raiden.raiden_account.get_book(
                token=transfer.currency
            )
            raiden_channel_book = payment.channel.account.get_book(token=transfer.currency)
            raiden_account_book.debits.create(**params)
            raiden_channel_book.credits.create(**params)
        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=RaidenTransferExecution)
@receiver(post_save, sender=BlockchainTransferExecution)
def on_external_transfer_executed_move_funds_from_treasury_to_external_address(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        if not transfer.address:
            logging.warning(f"External Transfer {transfer} marked as executed, but no address")
            return

        try:
            external_account, _ = ExternalAddressAccount.objects.get_or_create(
                address=transfer.address
            )

            treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)
            external_account_book = external_account.get_book(token=transfer.currency)
            params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

            treasury_book.debits.create(**params)
            external_account_book.credits.create(**params)

        except Exception as exc:
            logger.exception(exc)


@receiver(post_save, sender=TransferFailure)
@receiver(post_save, sender=TransferCancellation)
def on_reverted_transaction_move_funds_from_treasury_to_sender(sender, **kw):
    if kw["created"]:
        transfer_action = kw["instance"]
        transfer = transfer_action.transfer

        if transfer.is_processed:
            logger.critical(f"{transfer} has already been processed, yet has {transfer_action}")
            return

        try:
            treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)
            sender_book = transfer.sender.account.get_book(token=transfer.currency)
            treasury_book.debits.create(
                reference=transfer_action, currency=transfer.currency, amount=transfer.amount
            )
            sender_book.credits.create(
                reference=transfer_action, currency=transfer.currency, amount=transfer.amount
            )

        except Exception as exc:
            logger.exception(exc)


@receiver(account_deposit_received, sender=Transaction)
def on_account_deposit_received_record_entries(sender, **kw):
    account = kw["account"]
    amount = kw["amount"]
    transaction = kw["transaction"]

    chain = transaction.block.chain

    chain_book = chain.account.get_book(token=amount.currency)
    account_book = account.onchain_account.get_book(token=amount.currency)

    params = dict(reference=transaction, currency=amount.currency, amount=amount.amount)

    chain_book.debits.create(**params)
    account_book.credits.create(**params)


@receiver(outgoing_transfer_mined, sender=Transaction)
def on_blockchain_transfer_mined_move_funds_from_wallet_to_blockchain_acount(sender, **kw):
    wallet = kw["account"]
    amount = kw["amount"]
    transaction = kw["transaction"]

    try:
        wallet_book = wallet.onchain_account.get_book(token=amount.currency)
        blockchain_book = amount.currency.chain.account.get_book(token=amount.currency)
        params = dict(reference=transaction, currency=amount.currency, amount=amount.amount)
        wallet_book.debits.create(**params)
        blockchain_book.credits.create(**params)
    except Exception as exc:
        logger.exception(exc)


@receiver(post_save, sender=RaidenPayment)
def on_raiden_payment_record_entries_between_account_to_network(sender, **kw):
    if kw["created"]:
        payment = kw["instance"]

        raiden = payment.channel.raiden

        is_sent = payment.sender_address == raiden.address
        is_received = payment.receiver_address == raiden.address

        account_book = raiden.raiden_account.get_book(token=payment.token)
        channel_book = payment.channel.account.get_book(token=payment.token)
        params = dict(reference=payment, currency=payment.token, amount=payment.amount)

        if is_sent:
            account_book.debits.create(**params)
            channel_book.credits.create(**params)

        if is_received:
            account_book.credits.create(**params)
            channel_book.debits.create(**params)


__all__ = [
    "on_user_created_create_account",
    "on_chain_created_create_account",
    "on_raiden_created_create_account",
    "on_wallet_created_create_account",
    "on_payment_confirmed_record_entries",
    "on_account_deposit_received_record_entries",
    "on_reverted_transaction_move_funds_from_treasury_to_sender",
    "on_blockchain_transfer_mined_move_funds_from_wallet_to_blockchain_acount",
    "on_blockchain_transfer_executed_move_funds_from_wallet_to_blockchain",
    "on_blockchain_transfer_executed_record_fee_entries",
    "on_raiden_transfer_executed_move_funds_from_account_to_network",
    "on_internal_transfer_executed_move_funds_from_treasury_to_receiver",
    "on_external_transfer_executed_move_funds_from_treasury_to_external_address",
    "on_raiden_payment_record_entries_between_account_to_network",
]
