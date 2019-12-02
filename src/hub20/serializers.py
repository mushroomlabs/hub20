from typing import Dict

from django.db import transaction
from rest_framework import serializers

from blockchain.models import CURRENT_CHAIN_ID
from . import models


class EthereumTokenSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="hub20:token-detail", lookup_field="ticker", lookup_url_kwarg="code"
    )
    code = serializers.CharField(source="ticker")

    class Meta:
        model = models.EthereumToken
        fields = ["url", "code", "name", "address"]


class PaymentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="hub20:payment-detail")
    currency = serializers.PrimaryKeyRelatedField(
        queryset=models.EthereumToken.objects.filter(chain=CURRENT_CHAIN_ID)
    )
    transfer_methods = serializers.SerializerMethodField()

    def create(self, validated_data: Dict) -> models.Payment:
        request = self.context["request"]
        with transaction.atomic():
            return models.Payment.objects.create(
                wallet=models.Payment.get_wallet(),
                raiden=models.Payment.get_raiden(validated_data["currency"]),
                account=request.user,
                **validated_data,
            )

    def get_transfer_methods(self, obj: models.Payment) -> Dict:
        return {
            "blockchain": obj.chain_transfer_details,
            "raiden": obj.raiden_transfer_details,
        }

    class Meta:
        model = models.Payment
        fields = ["url", "amount", "currency", "expiration_time", "created", "transfer_methods"]
        read_only_fields = [
            "expiration_time",
            "created",
        ]


class PaymentReadSerializer(PaymentSerializer):
    currency = EthereumTokenSerializer(read_only=True)
