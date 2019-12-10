from typing import Dict
import copy

from django.contrib.auth import get_user_model
from django.db import transaction
from gnosis.eth.django.serializers import EthereumAddressField, HexadecimalField
from rest_framework import serializers
from rest_framework.reverse import reverse

from ethereum_money.serializers import (
    EthereumTokenSerializer,
    TokenValueField,
    CurrencyRelatedField,
)
from . import models

User = get_user_model()


class UserRelatedField(serializers.SlugRelatedField):
    queryset = User.objects.filter(is_active=True)

    def __init__(self, *args, **kw):
        kw.setdefault("slug_field", "username")
        super().__init__(*args, **kw)


class TokenBalanceSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()
    amount = TokenValueField(read_only=True)
    currency = EthereumTokenSerializer(read_only=True)
    balance = serializers.CharField(source="formatted", read_only=True)

    def get_url(self, obj):
        return reverse(
            "hub20:balance-detail",
            kwargs={"code": obj.currency.ticker},
            request=self.context.get("request"),
        )


class TransferSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:transfer-detail")
    address = EthereumAddressField(write_only=True, required=False)
    recipient = UserRelatedField(write_only=True, required=False, allow_null=True)
    currency = CurrencyRelatedField()
    target = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate_recipient(self, value):
        request = self.context["request"]
        if value == request.user:
            raise serializers.ValidationError("You can not make a transfer to yourself")
        return value

    def validate(self, data):
        address = data.get("address")
        recipient = data.get("recipient")
        request = self.context["request"]

        if not address and not recipient:
            raise serializers.ValidationError(
                "Either one of recipient or address must be provided"
            )
        if address and recipient:
            raise serializers.ValidationError(
                "Choose recipient by address or username, but not both at the same time"
            )

        transfer_data = copy.copy(data)
        del transfer_data["address"]
        del transfer_data["recipient"]

        if recipient is not None:
            transfer_class = models.InternalTransfer
            transfer_data["receiver"] = recipient
        else:
            transfer_class = models.ExternalTransfer
            transfer_data["recipient_address"] = address

        transfer = transfer_class(sender=request.user, **transfer_data)

        try:
            transfer.verify_conditions()
        except models.TransferError as exc:
            raise serializers.ValidationError(str(exc))

        return transfer_data

    def create(self, validated_data):
        transfer_class = (
            models.InternalTransfer if "recipient" in validated_data else models.ExternalTransfer
        )
        request = self.context["request"]

        return transfer_class.objects.create(sender=request.user, **validated_data)

    class Meta:
        model = models.Transfer
        fields = (
            "url",
            "address",
            "recipient",
            "amount",
            "currency",
            "memo",
            "identifier",
            "status",
            "target",
        )
        read_only_fields = ("recipient", "status", "target")


class PaymentOrderMethodSerializer(serializers.ModelSerializer):
    blockchain = EthereumAddressField(source="wallet.address", read_only=True)
    raiden = EthereumAddressField(source="raiden.address", read_only=True)
    identifier = serializers.IntegerField(read_only=True)
    expiration_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = models.PaymentOrderMethod
        fields = ("blockchain", "raiden", "identifier", "expiration_time")
        read_only_fields = ("blockchain", "raiden", "identifier", "expiration_time")


class PaymentSerializer(serializers.ModelSerializer):
    currency = EthereumTokenSerializer()

    class Meta:
        model = models.Payment
        fields = ("created", "currency", "amount")
        read_only_fields = ("created", "currency", "amount")


class InternalPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InternalPayment
        fields = PaymentSerializer.Meta.fields + ("user", "memo")
        read_only_fields = PaymentSerializer.Meta.read_only_fields + ("user", "memo")


class BlockchainPaymentSerializer(PaymentSerializer):
    transaction = HexadecimalField(read_only=True, source="transaction.hash")

    class Meta:
        model = models.BlockchainPayment
        fields = PaymentSerializer.Meta.fields + ("transaction",)
        read_only_fields = PaymentSerializer.Meta.read_only_fields + ("transaction",)


class RaidenPaymentSerializer(PaymentSerializer):
    raiden = serializers.CharField(source="payment.channel.raiden.address")
    identifier = serializers.CharField(source="payment.identifier")

    class Meta:
        model = models.RaidenPayment
        fields = PaymentSerializer.Meta.fields + ("raiden", "identifier")
        read_only_fields = PaymentSerializer.Meta.read_only_fields + ("raiden", "identifier")


class PaymentOrderSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:payment-order-detail")
    currency = CurrencyRelatedField()
    payment_method = PaymentOrderMethodSerializer(read_only=True)
    payments = serializers.SerializerMethodField()

    def create(self, validated_data: Dict) -> models.PaymentOrder:
        request = self.context["request"]
        with transaction.atomic():
            return models.PaymentOrder.objects.create(user=request.user, **validated_data)

    def get_payments(self, obj):
        def get_payment_serializer(payment):
            return {
                models.InternalPayment: InternalPaymentSerializer,
                models.BlockchainPayment: BlockchainPaymentSerializer,
                models.RaidenPayment: RaidenPaymentSerializer,
            }.get(type(payment), PaymentSerializer)(payment, context=self.context)

        return [get_payment_serializer(payment).data for payment in obj.payments]

    class Meta:
        model = models.PaymentOrder
        fields = [
            "url",
            "amount",
            "currency",
            "created",
            "payment_method",
            "payments",
            "status",
        ]
        read_only_fields = [
            "payment_method",
            "status",
            "created",
        ]


class PaymentOrderReadSerializer(PaymentOrderSerializer):
    currency = EthereumTokenSerializer(read_only=True)
