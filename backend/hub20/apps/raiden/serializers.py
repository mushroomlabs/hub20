from rest_framework import serializers

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.serializers import HexadecimalField
from hub20.apps.ethereum_money.app_settings import TRACKED_TOKENS
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
        view_name="token-network-detail", lookup_field="address"
    )
    token = HyperlinkedEthereumTokenSerializer()

    class Meta:
        model = models.TokenNetwork
        fields = ("url", "address", "token")
        read_only_fields = ("url", "address", "token")


class ServiceDepositSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="service-deposit-detail")
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
    url = serializers.HyperlinkedIdentityField(view_name="channel-detail")
    token = CurrencyRelatedField(queryset=None, source="token_network.token", read_only=True)

    class Meta:
        model = models.Channel
        fields = ("url", "token", "identifier", "partner_address", "status", "balance")
        read_only_fields = ("url", "token", "identifier", "partner_address", "status", "balance")


class ChannelManagementSerializer(serializers.ModelSerializer):
    channel = serializers.HyperlinkedRelatedField(view_name="channel-detail", read_only=True)
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
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        client = RaidenClient(obj)
        return client.get_status()

    class Meta:
        model = models.Raiden
        fields = ("address", "channels", "status")
        read_only_fields = ("address", "channels", "status")


class JoinTokenNetworkOrderSerializer(serializers.ModelSerializer):
    token_network = serializers.HyperlinkedRelatedField(
        view_name="token-network-detail", lookup_field="address", read_only=True
    )

    def get_token_network(self):
        view = self.context.get("view")
        return view and view.get_object()

    def create(self, validated_data):
        request = self.context["request"]
        token_network = self.get_token_network()
        raiden = models.Raiden.get()

        return self.Meta.model.objects.create(
            raiden=raiden, token_network=token_network, user=request.user, **validated_data
        )

    def validate(self, data):
        raiden = models.Raiden.get()
        token_network = self.get_token_network()

        if token_network in raiden.token_networks:
            raise serializers.ValidationError(
                f"Already joined token network {token_network.address}"
            )

        return data

    class Meta:
        model = models.JoinTokenNetworkOrder
        fields = ("id", "created", "token_network", "amount")
        read_only_fields = ("id", "created", "token_network")
