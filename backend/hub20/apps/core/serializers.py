from typing import Dict

from django.contrib.auth import get_user_model
from django.db import transaction
from ipware import get_client_ip
from rest_framework import serializers
from rest_framework.reverse import reverse

from hub20.apps.blockchain.serializers import EthereumAddressField, HexadecimalField
from hub20.apps.ethereum_money.models import EthereumTokenAmount
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


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-detail", lookup_field="username")

    class Meta:
        model = User
        fields = read_only_fields = ("url", "username", "first_name", "last_name", "email")


class TokenBalanceSerializer(EthereumTokenSerializer):
    balance = TokenValueField(read_only=True)

    class Meta:
        model = EthereumTokenSerializer.Meta.model
        fields = EthereumTokenSerializer.Meta.fields + ("balance",)
        read_only_fields = EthereumTokenSerializer.Meta.read_only_fields + ("balance",)


class HyperlinkedTokenBalanceSerializer(TokenBalanceSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return reverse(
            "balance-detail",
            kwargs={"address": obj.address},
            request=self.context.get("request"),
        )

    class Meta:
        model = TokenBalanceSerializer.Meta.model
        fields = ("url",) + TokenBalanceSerializer.Meta.fields
        read_only_fields = ("url",) + TokenBalanceSerializer.Meta.read_only_fields


class TransferSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="transfer-detail")
    address = EthereumAddressField(required=False, allow_null=True)
    recipient = UserRelatedField(source="receiver", required=False, allow_null=True)
    token = CurrencyRelatedField(source="currency")
    target = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate_recipient(self, value):
        request = self.context["request"]
        if value == request.user:
            raise serializers.ValidationError("You can not make a transfer to yourself")
        return value

    def validate(self, data):
        # Check if we have a valid recipient
        address = data.get("address", None)
        recipient = data.get("receiver", None)

        if not address and not recipient:
            raise serializers.ValidationError(
                "Either one of recipient or address must be provided"
            )
        if address and recipient:
            raise serializers.ValidationError(
                "Choose recipient by address or username, but not both at the same time"
            )

        # We do need to check the balance here though because the amount
        # corresponding to the transfer is deducted from the user's balance
        # upon creation for two reasons: keeping the accounting books balanced
        # and ensuring that users can not overdraw.

        # There is also the cost of transfer fees (especially for on-chain
        # transfers), but given that these can not be predicted and the hub
        # operator might waive the fees from the users, we do not do any
        # charging here and deduct fees only after the transaction is complete.
        request = self.context["request"]

        currency = data["currency"]
        transfer_amount = EthereumTokenAmount(currency=currency, amount=data["amount"])
        user_balance = request.user.account.get_balance(currency)

        if user_balance < transfer_amount:
            raise serializers.ValidationError("Insuffcient balance")

        return data

    def create(self, validated_data):
        request = self.context["request"]

        return self.Meta.model.objects.create(sender=request.user, **validated_data)

    class Meta:
        model = models.Transfer
        fields = (
            "id",
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
        read_only_fields = ("id", "status", "target")


class TransferExecutionSerializer(serializers.ModelSerializer):
    token = CurrencyRelatedField(source="transfer.currency")
    target = serializers.CharField(source="transfer.target", read_only=True)
    amount = TokenValueField(source="transfer.amount")

    class Meta:
        model = models.TransferExecution
        fields = read_only_fields = ("created", "token", "amount", "target")


class PaymentRouteSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="name", read_only=True)

    @staticmethod
    def get_serializer_class(route):
        return {
            models.InternalPaymentRoute: InternalPaymentRouteSerializer,
            models.BlockchainPaymentRoute: BlockchainPaymentRouteSerializer,
            models.RaidenPaymentRoute: RaidenPaymentRouteSerializer,
        }.get(type(route), PaymentRouteSerializer)


class InternalPaymentRouteSerializer(PaymentRouteSerializer):
    class Meta:
        model = models.InternalPaymentRoute
        fields = read_only_fields = ("recipient", "type")


class BlockchainPaymentRouteSerializer(PaymentRouteSerializer):
    address = EthereumAddressField(source="account.address", read_only=True)
    network_id = serializers.IntegerField(source="order.chain_id", read_only=True)
    start_block = serializers.IntegerField(source="start_block_number", read_only=True)
    expiration_block = serializers.IntegerField(source="expiration_block_number", read_only=True)

    class Meta:
        model = models.BlockchainPaymentRoute
        fields = read_only_fields = (
            "address",
            "network_id",
            "start_block",
            "expiration_block",
            "type",
        )


class RaidenPaymentRouteSerializer(PaymentRouteSerializer):
    address = EthereumAddressField(source="raiden.address", read_only=True)

    class Meta:
        model = models.RaidenPaymentRoute
        fields = read_only_fields = ("address", "expiration_time", "identifier", "type")


class PaymentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    url = serializers.HyperlinkedIdentityField(view_name="payments-detail")
    currency = EthereumTokenSerializer()
    confirmed = serializers.BooleanField(source="is_confirmed", read_only=True)

    class Meta:
        model = models.Payment
        fields = read_only_fields = (
            "id",
            "url",
            "created",
            "currency",
            "amount",
            "confirmed",
        )


class InternalPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InternalPayment
        fields = PaymentSerializer.Meta.fields + ("identifier", "user", "memo")
        read_only_fields = PaymentSerializer.Meta.read_only_fields + (
            "identifier",
            "user",
            "memo",
        )


class BlockchainPaymentSerializer(PaymentSerializer):
    transaction = HexadecimalField(source="transaction.hash", read_only=True)
    block = serializers.IntegerField(source="transaction.block.number", read_only=True)

    class Meta:
        model = models.BlockchainPayment
        fields = PaymentSerializer.Meta.fields + ("identifier", "transaction", "block")
        read_only_fields = PaymentSerializer.Meta.read_only_fields + (
            "identifier",
            "transaction",
            "block",
        )


class RaidenPaymentSerializer(PaymentSerializer):
    raiden = serializers.CharField(source="payment.channel.raiden.address")

    class Meta:
        model = models.RaidenPayment
        fields = PaymentSerializer.Meta.fields + ("identifier", "raiden")
        read_only_fields = PaymentSerializer.Meta.read_only_fields + (
            "identifier",
            "raiden",
        )


class DepositSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="deposit-detail")
    token = CurrencyRelatedField(source="currency")
    routes = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    def create(self, validated_data: Dict):
        request = self.context["request"]
        with transaction.atomic():
            return self.Meta.model.objects.create(
                user=request.user, session_key=request.session.session_key, **validated_data
            )

    def get_routes(self, obj):
        def get_route_serializer(route):
            serializer_class = PaymentRouteSerializer.get_serializer_class(route)
            return serializer_class(route, context=self.context)

        return [get_route_serializer(route).data for route in obj.routes.select_subclasses()]

    def get_payments(self, obj):
        def get_payment_serializer(payment):
            return {
                models.InternalPayment: InternalPaymentSerializer,
                models.BlockchainPayment: BlockchainPaymentSerializer,
                models.RaidenPayment: RaidenPaymentSerializer,
            }.get(type(payment), PaymentSerializer)(payment, context=self.context)

        return [get_payment_serializer(payment).data for payment in obj.payments]

    class Meta:
        model = models.Deposit
        fields = (
            "url",
            "id",
            "token",
            "created",
            "routes",
            "payments",
            "status",
        )
        read_only_fields = ("id", "created", "status")


class PaymentOrderSerializer(DepositSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="payment-order-detail")
    amount = TokenValueField()

    class Meta:
        model = models.PaymentOrder
        fields = DepositSerializer.Meta.fields + ("amount",)
        read_only_fields = DepositSerializer.Meta.read_only_fields


class PaymentOrderReadSerializer(PaymentOrderSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="payment-order-detail")


class PaymentConfirmationSerializer(serializers.ModelSerializer):
    token = CurrencyRelatedField(source="payment.currency")
    amount = TokenValueField(source="payment.amount")
    route = serializers.SerializerMethodField()

    def get_route(self, obj):
        route = models.PaymentRoute.objects.get_subclass(id=obj.payment.route_id)
        serializer_class = PaymentRouteSerializer.get_serializer_class(route)
        return serializer_class(route, context=self.context).data

    class Meta:
        model = models.PaymentConfirmation
        fields = read_only_fields = ("created", "token", "amount", "route")


class CheckoutSerializer(PaymentOrderSerializer):
    store = serializers.PrimaryKeyRelatedField(queryset=models.Store.objects.all())
    voucher = serializers.SerializerMethodField()

    def validate(self, data):
        currency = data["currency"]
        store = data["store"]
        if currency not in store.accepted_currencies.all():
            raise serializers.ValidationError(f"{currency.code} is not accepted at {store.name}")

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        client_ip, _ = get_client_ip(request)
        store = validated_data.pop("store")

        with transaction.atomic():
            return models.Checkout.objects.create(
                store=store,
                user=store.owner,
                session_key=request.session.session_key,
                requester_ip=client_ip,
                **validated_data,
            )

    def get_voucher(self, obj):
        return obj.issue_voucher()

    class Meta:
        model = models.Checkout
        fields = PaymentOrderSerializer.Meta.fields + (
            "store",
            "external_identifier",
            "voucher",
        )
        read_only_fields = PaymentOrderSerializer.Meta.read_only_fields + ("voucher",)


class HttpCheckoutSerializer(CheckoutSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="checkout-detail")

    class Meta:
        model = models.Checkout
        fields = ("url",) + CheckoutSerializer.Meta.fields
        read_only_fields = CheckoutSerializer.Meta.read_only_fields


class StoreSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="store-detail")
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


class BookEntrySerializer(serializers.ModelSerializer):
    amount = serializers.CharField(source="as_token_amount")
    reference_type = serializers.CharField(source="reference_type.model")
    reference = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return obj.__class__.__name__.lower()

    def get_summary(self, obj):
        return {
            models.Transfer: "transfer",
            models.TransferExecution: "transfer sent",
            models.PaymentConfirmation: "payment received",
        }.get(type(obj.reference))

    def get_reference(self, obj):
        params = {
            models.TransferExecution: lambda: {
                "viewname": "transfer-detail",
                "kwargs": {"pk": obj.reference.transfer.pk},
            },
            models.PaymentConfirmation: lambda: {
                "viewname": "payments-detail",
                "kwargs": {"pk": obj.reference.payment.pk},
            },
            models.Transfer: lambda: {
                "viewname": "transfer-detail",
                "kwargs": {"pk": obj.reference.pk},
            },
        }.get(type(obj.reference))

        return params and reverse(request=self.context.get("request"), **params())

    class Meta:
        read_only_fields = fields = (
            "id",
            "created",
            "amount",
            "type",
            "reference_type",
            "reference",
        )


class CreditSerializer(BookEntrySerializer):
    class Meta:
        model = models.Credit
        fields = read_only_fields = BookEntrySerializer.Meta.fields


class DebitSerializer(BookEntrySerializer):
    class Meta:
        model = models.Debit
        fields = read_only_fields = BookEntrySerializer.Meta.fields


class AccountingBookSerializer(EthereumTokenSerializer):
    total_credit = TokenValueField(read_only=True)
    total_debit = TokenValueField(read_only=True)
    balance = TokenValueField(read_only=True)

    class Meta:
        model = EthereumTokenSerializer.Meta.model
        fields = EthereumTokenSerializer.Meta.fields + ("total_credit", "total_debit", "balance")
        read_only_fields = EthereumTokenSerializer.Meta.fields + (
            "total_credit",
            "total_debit",
            "balance",
        )
