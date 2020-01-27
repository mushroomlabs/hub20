from rest_framework import serializers

from hub20.apps.blockchain.app_settings import CHAIN_ID

from . import models
from .app_settings import TRACKED_TOKENS


class TokenValueField(serializers.DecimalField):
    def __init__(self, *args, **kw):
        kw.setdefault("max_digits", 32)
        kw.setdefault("decimal_places", 18)
        super().__init__(*args, **kw)


class CurrencyRelatedField(serializers.SlugRelatedField):
    queryset = models.EthereumToken.objects.filter(chain=CHAIN_ID, ticker__in=TRACKED_TOKENS)

    def __init__(self, *args, **kw):
        kw.setdefault("slug_field", "ticker")
        super().__init__(*args, **kw)


class EthereumTokenSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="ticker")
    logo = serializers.URLField(source="coingecko.logo_url")
    network_id = serializers.IntegerField(source="chain")

    class Meta:
        model = models.EthereumToken
        fields = ("code", "name", "address", "network_id", "decimals", "logo")
        read_only_fields = ("code", "name", "address", "network_id", "decimals", "logo")


class ExchangeRateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(source="token.ticker")
    currency = serializers.CharField(source="currency_code")
    time = serializers.DateTimeField(source="created")

    class Meta:
        model = models.ExchangeRate
        fields = ("token", "currency", "rate", "time")
        read_only_fields = ("token", "currency", "rate", "time")
