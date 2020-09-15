import logging

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.models import Chain
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden.client.blockchain import get_service_token_address, mint_tokens
from hub20.apps.raiden.models import Raiden

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Mints the service token (RDN) on test networks"

    def handle(self, *args, **options):
        raiden = Raiden.get()

        w3 = get_web3()
        chain_id = int(w3.net.version)
        chain = Chain.make(chain_id)

        is_mainnet = chain.id == 1
        if is_mainnet:
            logger.error("Can only mint tokens on testnets")
            return

        service_token_address = get_service_token_address(chain_id)
        service_token = EthereumToken.make(service_token_address, chain)

        amount = EthereumTokenAmount(
            amount=app_settings.Raiden.minimum_service_token_required, currency=service_token
        )
        mint_tokens(w3=w3, raiden=raiden, amount=amount)
