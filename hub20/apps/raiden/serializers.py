from rest_framework import serializers

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.serializers import HexadecimalField
from hub20.apps.ethereum_money.client import get_account_balance
from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.ethereum_money.serializers import EthereumTokenAmountSerializer, TokenValueField
from hub20.apps.ethereum_money.typing import TokenAmount

from .client.blockchain import get_service_token
from .models import Raiden, ServiceDeposit


class RaidenSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="raiden:raiden-detail", lookup_field="address"
    )

    class Meta:
        model = Raiden
        fields = ("address", "url")
        read_only_fields = ("address", "url")


class DepositSerializer(EthereumTokenAmountSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="raiden:deposit-detail")
    raiden = serializers.HyperlinkedRelatedField(
        view_name="raiden:raiden-detail", queryset=Raiden.objects.all(), lookup_field="address",
    )
    transaction = HexadecimalField(read_only=True, source="transaction.hash")

    class Meta:
        model = ServiceDeposit
        fields = ("url", "created", "raiden", "amount", "currency", "transaction")
        read_only_fields = ("url", "created", "raiden", "amount", "currency", "transaction")


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
