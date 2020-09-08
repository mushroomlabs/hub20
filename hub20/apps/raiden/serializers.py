from rest_framework import serializers

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.serializers import HexadecimalField
from hub20.apps.ethereum_money.app_settings import TRACKED_TOKENS
from hub20.apps.ethereum_money.client import get_account_balance
from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.ethereum_money.serializers import (
    CurrencyRelatedField,
    EthereumTokenSerializer,
    HyperlinkedEthereumTokenSerializer,
    TokenValueField,
)
from hub20.apps.ethereum_money.typing import TokenAmount

from . import models
from .client.blockchain import get_service_token
from .client.node import RaidenClient


class TokenNetworkField(serializers.RelatedField):
    queryset = models.TokenNetwork.objects.filter(token__address__in=TRACKED_TOKENS)
    lookup_field = "address"


class TokenNetworkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="raiden:token-network-detail", lookup_field="address"
    )
    token = HyperlinkedEthereumTokenSerializer()

    class Meta:
        model = models.TokenNetwork
        fields = ("url", "address", "token")
        read_only_fields = ("url", "address", "token")


class ServiceDepositSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="raiden:service-deposit-detail")
    transaction = HexadecimalField(read_only=True, source="result.transaction.hash")
    token = EthereumTokenSerializer(source="currency", read_only=True)
    amount = TokenValueField()

    def create(self, validated_data):
        raiden = models.Raiden.get()
        request = self.context.get("request")
        w3 = get_web3()
        token = get_service_token(w3=w3)

        return self.Meta.model.objects.create(
            raiden=raiden, user=request.user, currency=token, **validated_data
        )

    class Meta:
        model = models.UserDepositContractOrder
        fields = ("url", "created", "amount", "token", "transaction")
        read_only_fields = ("url", "created", "token", "transaction")


class ChannelSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="raiden:channel-detail")
    token = CurrencyRelatedField(queryset=None, source="token_network.token", read_only=True)

    class Meta:
        model = models.Channel
        fields = ("url", "token", "identifier", "partner_address", "status", "balance")
        read_only_fields = ("url", "token", "identifier", "partner_address", "status", "balance")


class ChannelManagementSerializer(serializers.ModelSerializer):
    channel = serializers.HyperlinkedRelatedField(
        view_name="raiden:channel-detail", read_only=True
    )
    amount = TokenValueField()

    def create(self, validated_data):
        channel = self.get_channel()
        request = self.context["request"]

        return self.Meta.model.objects.create(
            raiden=channel.raiden, channel=channel, user=request.user, **validated_data
        )

    def get_channel(self):
        view = self.context.get("view")
        return view and view.get_object()


class ChannelDepositSerializer(ChannelManagementSerializer):
    class Meta:
        model = models.ChannelDepositOrder
        fields = ("id", "created", "channel", "amount")
        read_only_fields = ("id", "created", "channel")


class ChannelWithdrawSerializer(ChannelManagementSerializer):
    class Meta:
        model = models.ChannelWithdrawOrder
        fields = ("created", "channel", "amount")
        read_only_fields = ("created", "channel")

    def validate_amount(self, data):
        channel = self.get_channel()
        if channel is None:
            raise serializers.ValidationError("Can not get channel information")

        token = channel.token
        amount = TokenAmount(data).normalize()
        withdraw_amount = EthereumTokenAmount(amount=amount, currency=token)
        channel_balance = EthereumTokenAmount(amount=channel.balance, currency=token)

        if withdraw_amount > channel_balance:
            raise serializers.ValidationError(f"Insufficient balance: {channel_balance.formatted}")

        return data


class RaidenSerializer(serializers.ModelSerializer):
    channels = ChannelSerializer(many=True)
    chain = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_chain(self, obj):
        w3 = get_web3()
        return int(w3.net.version)

    def get_status(self, obj):
        client = RaidenClient(obj)
        return client.get_status()

    class Meta:
        model = models.Raiden
        fields = ("address", "chain", "channels", "status")
        read_only_fields = ("address", "channels", "status")


class TokenNetworkConnectionSerializer(serializers.Serializer):
    token_network = TokenNetworkField()
    amount = TokenValueField(write_only=True)

    def validate(self, data):
        w3 = get_web3()
        token = get_service_token(w3=w3)

        raiden_account = data["raiden"]
        amount = TokenAmount(data["amount"]).normalize()
        deposit_amount = EthereumTokenAmount(amount=amount, currency=token)
        token_balance = get_account_balance(w3=w3, token=token, address=raiden_account.address)

        if token_balance < deposit_amount:
            raise serializers.ValidationError(f"Insufficient balance: {token_balance.formatted}")

        return data
