from rest_framework import serializers

from hub20.apps.blockchain.serializers import EthereumAddressField

from . import get_ethereum_account_model, models


class TokenValueField(serializers.DecimalField):
    def __init__(self, *args, **kw):
        kw.setdefault("max_digits", 32)
        kw.setdefault("decimal_places", 18)
        super().__init__(*args, **kw)


class CurrencyRelatedField(serializers.SlugRelatedField):
    queryset = models.EthereumToken.tracked.all()

    def __init__(self, *args, **kw):
        kw.setdefault("slug_field", "address")
        super().__init__(*args, **kw)


class EthereumTokenSerializer(serializers.ModelSerializer):
    network_id = serializers.IntegerField(source="chain_id")

    class Meta:
        model = models.EthereumToken
        fields = ("code", "name", "address", "network_id", "decimals")
        read_only_fields = ("code", "name", "address", "network_id", "decimals")


class EthereumTokenAmountSerializer(serializers.ModelSerializer):
    currency = CurrencyRelatedField()
    amount = TokenValueField()


class HyperlinkedEthereumTokenSerializer(EthereumTokenSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="ethereum_money:token-detail", lookup_field="address"
    )

    class Meta:
        model = models.EthereumToken
        fields = ("url",) + EthereumTokenSerializer.Meta.fields
        read_only_fields = ("url",) + EthereumTokenSerializer.Meta.read_only_fields


class EthereumAccountSerializer(serializers.ModelSerializer):
    address = EthereumAddressField()

    class Meta:
        model = get_ethereum_account_model()
        fields = read_only_fields = ("address",)
