import logging

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.app_settings import CHAIN_ID
from hub20.apps.blockchain.choices import ETHEREUM_CHAINS
from hub20.apps.ethereum_money.models import CoingeckoDefinition, EthereumToken

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches data from specific token on coingecko"

    def add_arguments(self, parser):
        parser.add_argument("-t", "--token", required=True, help="Token Ticker")

    def handle(self, *args, **options):
        symbol = options["token"]
        if CHAIN_ID != ETHEREUM_CHAINS.mainnet:
            print(
                "We can only load coingecko token data when connected to Mainnet, "
                f"and we are now connected to {ETHEREUM_CHAINS[CHAIN_ID]}"
            )
            return

        token = EthereumToken.objects.filter(ticker=symbol, chain=CHAIN_ID).first()

        if not token:
            print(f"{symbol} not found on database")
            return

        CoingeckoDefinition.make_definition(token)
