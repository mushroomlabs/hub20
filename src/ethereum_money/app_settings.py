from django.conf import settings

TRANSFER_GAS_LIMIT = getattr(settings, "ETHEREUM_MONEY_TRANSFER_GAS_LIMIT", 200_000)
