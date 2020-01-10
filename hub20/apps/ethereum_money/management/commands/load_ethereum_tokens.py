import logging
import time

from django.core.management.base import BaseCommand
from pycoingecko import CoinGeckoAPI

from hub20.apps.blockchain.app_settings import CHAIN_ID
from hub20.apps.blockchain.choices import ETHEREUM_CHAINS
from hub20.apps.ethereum_money.models import CoingeckoDefinition

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches all data from ERC20 tokens via coingecko"

    def handle(self, *args, **options):
        if CHAIN_ID != ETHEREUM_CHAINS.mainnet:
            print(
                "We can only load coingecko token data when connected to Mainnet, "
                f"and we are now connected to {ETHEREUM_CHAINS[CHAIN_ID]}"
            )
            return

        gecko = CoinGeckoAPI()
        recorded_coins = CoingeckoDefinition.objects.values_list("slug", flat=True)
        gecko_coins = [coin["id"] for coin in gecko.get_coins_list()]
        coins_to_process = set(gecko_coins) - set(recorded_coins)

        for coin_id in coins_to_process:
            coin_data = gecko.get_coin_by_id(coin_id)
            is_ethereum = all(
                [coin_data["asset_platform_id"] == "ethereum", "contract_address" in coin_data]
            )
            if is_ethereum:
                try:
                    definition = CoingeckoDefinition.process(coin_data)
                    logger.info(f"Processed {definition.token.ticker} definition")
                except Exception as exc:
                    logger.error(f"Error processing {coin_id}: {exc}")

            time.sleep(0.5)
