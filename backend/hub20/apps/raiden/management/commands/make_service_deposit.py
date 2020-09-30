import getpass
import logging

import ethereum
from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address

from hub20.apps.blockchain.client import get_web3
from hub20.apps.ethereum_money.models import EthereumTokenAmount, KeystoreAccount
from hub20.apps.raiden.client.blockchain import get_service_token, make_service_deposit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deposits RDN at Raiden Service Contract"

    def add_arguments(self, parser):
        parser.add_argument("-a", "--account", required=True, type=str)
        parser.add_argument("--amount", default=1000, type=int)

    def handle(self, *args, **options):
        address = to_checksum_address(options["account"])
        account = KeystoreAccount.objects.filter(address=address).first()

        if not account:
            private_key = getpass.getpass(f"Private Key for {address} required: ")
            generated_address = to_checksum_address(ethereum.utils.privtoaddr(private_key.strip()))
            assert generated_address == address, "Private Key does not match"
            account = KeystoreAccount(address=address, private_key=private_key)

        w3 = get_web3()

        token = get_service_token(w3=w3)

        amount = EthereumTokenAmount(amount=options["amount"], currency=token)
        make_service_deposit(w3=w3, account=account, amount=amount)
