import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.db.transaction import atomic
from django.dispatch import receiver

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.core.models.accounting import (
    ExternalAddressAccount,
    RaidenClientAccount,
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
from hub20.apps.ethereum_money.models import (
    BaseEthereumAccount,
    HierarchicalDeterministicWallet,
    KeystoreAccount,
)
from hub20.apps.ethereum_money.signals import account_deposit_received
from hub20.apps.raiden.models import Payment as RaidenPayment, Raiden

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def on_user_created_create_account(sender, **kw):
    if kw["created"]:
        UserAccount.objects.get_or_create(user=kw["instance"])


@receiver(post_save, sender=Chain)
def on_chain_created_create_treasury(sender, **kw):
    if kw["created"]:
        Treasury.objects.get_or_create(chain=kw["instance"])


@receiver(post_save, sender=Raiden)
def on_raiden_created_create_account(sender, **kw):
    if kw["created"]:
        RaidenClientAccount.objects.get_or_create(raiden=kw["instance"])


@receiver(post_save, sender=HierarchicalDeterministicWallet)
@receiver(post_save, sender=KeystoreAccount)
@receiver(post_save, sender=BaseEthereumAccount)
@receiver(post_save, sender=Raiden)
def on_wallet_created_create_account(sender, **kw):
    if kw["created"]:
        WalletAccount.objects.get_or_create(account=kw["instance"])


# In-Flows
@atomic()
@receiver(account_deposit_received, sender=Transaction)
def on_blockchain_deposit_received_move_funds_from_external_address_to_wallet(sender, **kw):
    wallet = kw["account"]
    amount = kw["amount"]
    transaction = kw["transaction"]

    params = dict(reference=transaction, currency=amount.currency, amount=amount.amount)
    external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
        address=transaction.from_address
    )

    external_address_book = external_address_account.get_book(token=amount.currency)
    wallet_book = wallet.onchain_account.get_book(token=amount.currency)

    external_address_book.debits.create(**params)
    wallet_book.credits.create(**params)


@atomic()
@receiver(post_save, sender=RaidenPayment)
def on_raiden_payment_received_move_funds_from_external_address_to_raiden(sender, **kw):
    if kw["created"]:
        payment = kw["instance"]
        raiden = payment.channel.raiden

        is_received = payment.receiver_address == raiden.address

        if is_received:
            params = dict(reference=payment, currency=payment.token, amount=payment.amount)

            external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
                address=payment.sender_address
            )

            external_account_book = external_address_account.get_book(token=payment.token)
            raiden_book = raiden.raiden_account.get_book(token=payment.token)

            external_account_book.debits.create(**params)
            raiden_book.credits.create(**params)


# Out-flows
@atomic()
@receiver(post_save, sender=BlockchainTransferExecution)
def on_blockchain_transfer_executed_move_funds_from_wallet_to_external_address(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)
        wallet = BaseEthereumAccount.objects.get(address=execution.transaction.from_address)
        external_account, _ = ExternalAddressAccount.objects.get_or_create(
            address=transfer.address
        )

        wallet_book = wallet.onchain_account.get_book(token=transfer.currency)
        external_account_book = external_account.get_book(token=transfer.currency)

        wallet_book.debits.create(**params)
        external_account_book.credits.create(**params)


@atomic()
@receiver(post_save, sender=RaidenTransferExecution)
def on_raiden_transfer_executed_move_funds_from_raiden_to_external_address(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        payment = execution.raidentransferexecution.payment
        params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

        external_account, _ = ExternalAddressAccount.objects.get_or_create(
            address=transfer.address
        )

        external_account_book = external_account.get_book(token=transfer.currency)
        raiden_book = payment.channel.raiden.raiden_account.get_book(token=transfer.currency)

        raiden_book.debits.create(**params)
        external_account_book.credits.create(**params)


@atomic()
@receiver(post_save, sender=BlockchainTransferExecution)
def on_blockchain_transfer_executed_record_fee_entries(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transaction = execution.transaction

        fee = execution.fee
        ETH = execution.fee.currency
        wallet = BaseEthereumAccount.objects.get(address=transaction.from_address)
        fee_account = ExternalAddressAccount.get_transaction_fee_account()

        wallet_book = wallet.onchain_account.get_book(token=ETH)
        fee_book = fee_account.get_book(token=ETH)
        treasury_book = transaction.block.chain.treasury.get_book(token=ETH)
        sender_book = execution.transfer.sender.account.get_book(token=ETH)

        params = dict(reference=transaction, currency=ETH, amount=fee.amount)

        # Entry: sender -> treasury
        sender_book.debits.create(**params)
        treasury_book.credits.create(**params)

        # Entry: wallet -> fee account
        wallet_book.debits.create(**params)
        fee_book.credits.create(**params)


# Internal movements
@atomic()
@receiver(post_save, sender=Transfer)
def on_transfer_created_move_funds_from_sender_to_treasury(sender, **kw):
    if kw["created"]:
        transfer = kw["instance"]
        params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

        user_book = transfer.sender.account.get_book(token=transfer.currency)
        treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)

        user_book.debits.create(**params)
        treasury_book.credits.create(**params)


@atomic()
@receiver(post_save, sender=TransferExecution)
def on_internal_transfer_executed_move_funds_from_treasury_to_receiver(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer

        if not transfer.receiver:
            logging.warning("Expected Internal Transfer, but no receiver user defined")
            return

        params = dict(reference=transfer, currency=transfer.currency, amount=transfer.amount)

        treasury_book = transfer.currency.chain.treasury.get_book(token=transfer.currency)
        receiver_book = transfer.receiver.account.get_book(token=transfer.currency)

        treasury_book.debits.create(**params)
        receiver_book.credits.create(**params)


@atomic()
@receiver(post_save, sender=PaymentConfirmation)
def on_payment_confirmed_move_funds_from_treasury_to_payee(sender, **kw):
    if kw["created"]:
        confirmation = kw["instance"]
        payment = confirmation.payment

        is_raiden_payment = hasattr(payment.route, "raidenpaymentroute")
        is_blockchain_payment = hasattr(payment.route, "blockchainpaymentroute")

        if is_raiden_payment or is_blockchain_payment:
            params = dict(reference=confirmation, amount=payment.amount, currency=payment.currency)
            treasury_book = payment.currency.chain.treasury.get_book(token=payment.currency)
            payee_book = payment.route.deposit.user.account.get_book(token=payment.currency)
            treasury_book.debits.create(**params)
            payee_book.credits.create(**params)
        else:
            logger.info(f"Payment {payment} was not routed through any external network")


@atomic()
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


__all__ = [
    "on_user_created_create_account",
    "on_chain_created_create_treasury",
    "on_raiden_created_create_account",
    "on_wallet_created_create_account",
    "on_blockchain_deposit_received_move_funds_from_external_address_to_wallet",
    "on_raiden_payment_received_move_funds_from_external_address_to_raiden",
    "on_blockchain_transfer_executed_move_funds_from_wallet_to_external_address",
    "on_raiden_transfer_executed_move_funds_from_raiden_to_external_address",
    "on_blockchain_transfer_executed_record_fee_entries",
    "on_transfer_created_move_funds_from_sender_to_treasury",
    "on_internal_transfer_executed_move_funds_from_treasury_to_receiver",
    "on_payment_confirmed_move_funds_from_treasury_to_payee",
    "on_reverted_transaction_move_funds_from_treasury_to_sender",
]
