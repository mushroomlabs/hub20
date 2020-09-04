from rest_framework import serializers

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.serializers import HexadecimalField
from hub20.apps.ethereum_money.client import get_account_balance
from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.ethereum_money.serializers import (
    CurrencyRelatedField,
    EthereumTokenAmountSerializer,
    TokenValueField,
)
from hub20.apps.ethereum_money.typing import TokenAmount

from .client.blockchain import get_service_token
from .models import Channel, Raiden, ServiceDeposit


class HyperlinkedRaidenField(serializers.HyperlinkedIdentityField):
    lookup_field = "address"

    def __init__(self, **kw):
        super().__init__(view_name="raiden:raiden-detail", **kw)


class HyperlinkedRelatedRaidenField(serializers.HyperlinkedRelatedField):
    view_name = "raiden:raiden-detail"
    lookup_field = "address"


class RaidenSerializer(serializers.ModelSerializer):
    url = HyperlinkedRaidenField()

    class Meta:
        model = Raiden
        fields = ("address", "url")
        read_only_fields = ("address", "url")


class DepositSerializer(EthereumTokenAmountSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="raiden:deposit-detail")
    raiden = HyperlinkedRelatedRaidenField(read_only=True)
    transaction = HexadecimalField(read_only=True, source="transaction.hash")

    class Meta:
        model = ServiceDeposit
        fields = ("url", "created", "raiden", "amount", "currency", "transaction")
        read_only_fields = ("url", "created", "raiden", "amount", "currency", "transaction")


class ChannelSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="raiden:channel-detail")
    raiden = HyperlinkedRelatedRaidenField(read_only=True)
    token = CurrencyRelatedField(queryset=None, source="token_network.token", read_only=True)

    class Meta:
        model = Channel
        fields = ("url", "raiden", "token", "status", "balance")
        read_only_fields = ("url", "raiden", "token", "status", "balance")


class ServiceDepositTaskSerializer(serializers.Serializer):
    raiden = serializers.ChoiceField(choices=Raiden.objects.all())
    amount = TokenValueField()

    def validate(self, data):
        w3 = get_web3()
        token = get_service_token(w3=w3)

        raiden_node = data["raiden"]
        amount = TokenAmount(data["amount"]).normalize()
        deposit_amount = EthereumTokenAmount(amount=amount, currency=token)
        token_balance = get_account_balance(w3=w3, token=token, address=raiden_node.address)

        if token_balance < deposit_amount:
            raise serializers.ValidationError(f"Insufficient balance: {token_balance.formatted}")

        return data
