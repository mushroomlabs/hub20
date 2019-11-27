from typing import Dict

from django.db import transaction
from rest_framework import serializers

from . import models


class EthereumTokenSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="hub20:token-detail", lookup_field="ticker", lookup_url_kwarg="code"
    )
    code = serializers.CharField(source="ticker")

    class Meta:
        model = models.EthereumToken
        fields = ["url", "code", "name", "address"]


class InvoiceSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:invoice-detail")

    def create(self, validated_data: Dict) -> models.Invoice:
        request = self.context["request"]
        with transaction.atomic():
            return models.Invoice.objects.create(
                wallet=models.Invoice.get_wallet(),
                raiden=models.Invoice.get_raiden(validated_data["currency"]),
                account=request.user,
                **validated_data,
            )

    class Meta:
        model = models.Invoice
        fields = [
            "url",
            "identifier",
            "amount",
            "currency",
            "expiration_time",
            "chain_payment_address",
            "raiden_payment_address",
            "created",
            "expired",
            "paid",
        ]
        read_only_fields = [
            "chain_payment_address",
            "raiden_payment_address",
            "expiration_time",
            "created",
            "expired",
            "paid",
        ]


class InvoiceReadSerializer(InvoiceSerializer):
    currency = EthereumTokenSerializer(read_only=True)
