import logging

from django.core.management.base import BaseCommand

from hub20.apps.ethereum_money import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches exchange rate from specific token/currency pair on coingecko"

    def add_arguments(self, parser):
        parser.add_argument("-t", "--token", required=True, help="Token Ticker")
        parser.add_argument("-c", "--currency", required=True, help="Currency code")

    def handle(self, *args, **options):
        tasks.get_exchange_rate(token_code=options["token"], currency_codes=[options["currency"]])
