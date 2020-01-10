import logging

from celery import shared_task
from pycoingecko import CoinGeckoAPI

from hub20.apps.blockchain.choices import ETHEREUM_CHAINS
from hub20.apps.ethereum_money.app_settings import TRACKED_FIAT_CURRENCIES, TRACKED_TOKENS
from hub20.apps.ethereum_money.models import CoingeckoDefinition, EthereumToken

logger = logging.getLogger(__name__)


@shared_task
def get_exchange_rates():
    CoingeckoDefinition.assert_mainnet()

    for token_code in TRACKED_TOKENS:
        get_exchange_rate(token_code, TRACKED_FIAT_CURRENCIES)


@shared_task
def get_exchange_rate(token_code, currency_codes):
    CoingeckoDefinition.assert_mainnet()

    token = EthereumToken.objects.filter(ticker=token_code, chain=ETHEREUM_CHAINS.mainnet).first()

    if not token:
        logger.info(f"{token_code} not found on database")
        return

    try:
        token_id = token.coingecko.slug
    except EthereumToken.coingecko.RelatedObjectDoesNotExist:
        CoingeckoDefinition.make_definition(token)
        token_id = token.coingecko.slug

    gecko = CoinGeckoAPI()

    prices = gecko.get_price(token_id, vs_currencies=currency_codes)
    token_prices = prices.get(token_id)

    for currency_code in currency_codes:
        token_currency_price = token_prices.get(currency_code.lower())

        if token_currency_price:
            rate = token.exchangerate_set.create(
                currency_code=currency_code.upper(), rate=token_currency_price
            )
            logger.info(f"Rate fetched successfully: {rate}")
