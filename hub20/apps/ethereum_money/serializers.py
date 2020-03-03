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
    queryset = models.EthereumToken.objects.filter(chain=CHAIN_ID, address__in=TRACKED_TOKENS)

    def __init__(self, *args, **kw):
        kw.setdefault("slug_field", "address")
        super().__init__(*args, **kw)


class EthereumTokenSerializer(serializers.ModelSerializer):
    network_id = serializers.IntegerField(source="chain")

    class Meta:
        model = models.EthereumToken
        fields = ("code", "name", "address", "network_id", "decimals")
        read_only_fields = ("code", "name", "address", "network_id", "decimals")


class HyperlinkedEthereumTokenSerializer(EthereumTokenSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="ethereum_money:token-detail", lookup_field="address"
    )

    class Meta:
        model = models.EthereumToken
        fields = ("url",) + EthereumTokenSerializer.Meta.fields
        read_only_fields = ("url",) + EthereumTokenSerializer.Meta.read_only_fields
