import copy
from typing import Dict

from django.contrib.auth import get_user_model
from django.db import transaction
from ipware import get_client_ip
from rest_framework import serializers
from rest_framework.reverse import reverse

from hub20.apps.blockchain.serializers import EthereumAddressField, HexadecimalField
from hub20.apps.ethereum_money.serializers import (
    CurrencyRelatedField,
    EthereumTokenSerializer,
    TokenValueField,
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
            kwargs={"code": obj.currency.code},
            request=self.context.get("request"),
        )


class TransferSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:transfer-detail")
    address = EthereumAddressField(write_only=True, required=False)
    recipient = UserRelatedField(write_only=True, required=False, allow_null=True)
    token = CurrencyRelatedField()
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
            "token",
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
    id = serializers.UUIDField()
    url = serializers.HyperlinkedIdentityField(view_name="hub20:payments-detail")
    currency = EthereumTokenSerializer()
    identifier = serializers.CharField()
    confirmed = serializers.BooleanField(source="is_confirmed")

    class Meta:
        model = models.Payment
        fields = ("id", "url", "created", "currency", "amount", "identifier", "route", "confirmed")
        read_only_fields = (
            "id",
            "url",
            "created",
            "currency",
            "amount",
            "identifier",
            "route",
            "confirmed",
        )


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

    class Meta:
        model = models.RaidenPayment
        fields = PaymentSerializer.Meta.fields + ("raiden",)
        read_only_fields = PaymentSerializer.Meta.read_only_fields + ("raiden",)


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
        fields = ["url", "amount", "currency", "created", "payment_method", "payments", "status"]
        read_only_fields = ["payment_method", "status", "created"]


class PaymentOrderReadSerializer(PaymentOrderSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:payment-order-detail")
    currency = EthereumTokenSerializer(read_only=True)


class CheckoutSerializer(serializers.ModelSerializer):
    store = serializers.PrimaryKeyRelatedField(queryset=models.Store.objects.all())
    token = CurrencyRelatedField(source="payment_order.currency")
    amount = TokenValueField(source="payment_order.amount")
    status = serializers.CharField(source="payment_order.status", read_only=True)
    payment_method = PaymentOrderMethodSerializer(
        source="payment_order.payment_method", read_only=True
    )
    payments = PaymentSerializer(many=True, source="payment_order.payments", read_only=True)
    voucher = serializers.SerializerMethodField()

    def validate(self, data):
        token = data["payment_order"]["currency"]
        store = data["store"]
        if token not in store.accepted_currencies.all():
            raise serializers.ValidationError(f"{token.code} is not accepted at {store.name}")

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        client_ip, _ = get_client_ip(request)
        store = validated_data["store"]
        with transaction.atomic():
            payment_order = models.PaymentOrder.objects.create(
                user=store.owner, **validated_data["payment_order"]
            )

            return models.Checkout.objects.create(
                store=store,
                external_identifier=validated_data["external_identifier"],
                payment_order=payment_order,
                requester_ip=client_ip,
            )

    def get_voucher(self, obj):
        return obj.issue_voucher()

    class Meta:
        model = models.Checkout
        fields = (
            "id",
            "created",
            "store",
            "external_identifier",
            "token",
            "amount",
            "payment_method",
            "payments",
            "status",
            "voucher",
        )
        read_only_fields = ("id",)


class HttpCheckoutSerializer(CheckoutSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:checkout-detail")

    class Meta:
        model = models.Checkout
        fields = ("url",) + CheckoutSerializer.Meta.fields
        read_only_fields = CheckoutSerializer.Meta.read_only_fields


class StoreSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:store-detail")
    site_url = serializers.URLField(source="url")
    public_key = serializers.CharField(source="rsa.public_key_pem", read_only=True)
    accepted_currencies = CurrencyRelatedField(many=True)

    def create(self, validated_data):
        request = self.context.get("request")
        currencies = validated_data.pop("accepted_currencies", [])
        store = models.Store.objects.create(owner=request.user, **validated_data)
        store.accepted_currencies.set(currencies)
        return store

    class Meta:
        model = models.Store
        fields = ("id", "url", "name", "site_url", "public_key", "accepted_currencies")
        read_only_fields = ("id", "public_key")
