import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.core.models.accounting import (
    ExternalAddressAccount,
    RaidenClientAccount,
    Treasury,
    UserAccount,
    WalletAccount,
)
from hub20.apps.ethereum_money.models import BaseEthereumAccount, EthereumToken
from hub20.apps.raiden.models import Payment as RaidenPayment, Raiden

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sets up accounting books and reconciles transactions and raiden payments"

    def handle(self, *args, **options):
        accounts = BaseEthereumAccount.objects.all()
        for user in User.objects.all():
            UserAccount.objects.get_or_create(user=user)

        for wallet in accounts:
            WalletAccount.objects.get_or_create(account=wallet)

        raiden = Raiden.get()
        RaidenClientAccount.objects.get_or_create(raiden=raiden)

        chain = Chain.make()
        Treasury.objects.get_or_create(chain=chain)

        transaction_type = ContentType.objects.get_for_model(Transaction)

        # Ethereum Transactions
        accounts_by_address = {acc.address: acc for acc in accounts}
        ETH = EthereumToken.ETH(chain=chain)
        for tx in Transaction.objects.filter(to_address__in=accounts.values("address")):
            amount = ETH.from_wei(tx.value)
            params = dict(
                reference_type=transaction_type,
                reference_id=tx.id,
                currency=ETH,
                amount=amount.amount,
            )
            external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
                address=tx.from_address
            )

            wallet = accounts_by_address[tx.to_address]
            external_address_book = external_address_account.get_book(token=ETH)
            wallet_book = wallet.onchain_account.get_book(token=ETH)

            external_address_book.debits.get_or_create(**params)
            wallet_book.credits.get_or_create(**params)

        # ERC20 Transactions
        tokens = EthereumToken.ERC20tokens.all()
        tokens_by_address = {token.address: token for token in tokens}

        for tx in Transaction.objects.filter(to_address__in=tokens.values("address")):
            token = tokens_by_address[tx.to_address]
            recipient_address, amount = token._decode_transaction(tx)
            is_token_transfer = recipient_address is not None and amount is not None

            wallet = BaseEthereumAccount.objects.filter(address=recipient_address).first()
            if is_token_transfer and wallet:
                external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
                    address=tx.from_address
                )

                external_address_book = external_address_account.get_book(token=token)
                wallet_book = wallet.onchain_account.get_book(token=token)

                params = dict(
                    reference_type=transaction_type,
                    reference_id=tx.id,
                    currency=token,
                    amount=amount.amount,
                )
                external_address_book.debits.get_or_create(**params)
                wallet_book.credits.get_or_create(**params)

        # Raiden payments
        payment_type = ContentType.objects.get_for_model(RaidenPayment)
        for channel in raiden.channels.all():
            logger.info(f"Recording entries for {channel}")
            for payment in channel.payments.all():
                logger.info(f"Recording entries for {payment}")
                params = dict(
                    reference_type=payment_type,
                    reference_id=payment.id,
                    amount=payment.amount,
                    currency=payment.token,
                )

                external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
                    address=payment.partner_address
                )

                external_account_book = external_address_account.get_book(token=payment.token)
                raiden_book = raiden.raiden_account.get_book(token=payment.token)

                if payment.is_outgoing:
                    raiden_book.debits.get_or_create(**params)
                    external_account_book.credits.get_or_create(**params)
                else:
                    external_account_book.debits.get_or_create(**params)
                    raiden_book.credits.get_or_create(**params)
