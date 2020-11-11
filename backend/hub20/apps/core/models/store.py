import datetime
import uuid
from typing import Optional

import jwt
from Crypto.PublicKey import RSA
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from hub20.apps.ethereum_money.models import EthereumToken

from .payments import PaymentOrder


class Store(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=300)
    url = models.URLField()
    accepted_currencies = models.ManyToManyField(EthereumToken)

    def __str__(self):
        return f"{self.name} ({self.url})"


class StoreRSAKeyPair(models.Model):
    DEFAULT_KEY_SIZE = 2048

    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name="rsa")
    public_key_pem = models.TextField()
    private_key_pem = models.TextField()

    @classmethod
    def generate(cls, store: Store, keysize: Optional[int] = None):
        bits = keysize or cls.DEFAULT_KEY_SIZE
        key = RSA.generate(bits)
        public_key_pem = key.publickey().export_key().decode()
        private_key_pem = key.export_key().decode()

        pair, _ = cls.objects.update_or_create(
            store=store,
            defaults={"public_key_pem": public_key_pem, "private_key_pem": private_key_pem},
        )
        return pair


class Checkout(PaymentOrder):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    external_identifier = models.TextField()
    requester_ip = models.GenericIPAddressField(null=True)

    def clean(self):
        if self.store.owner != self.user:
            raise ValidationError("Creator of payment order must be the same as store owner")

        if self.currency not in self.store.accepted_currencies.all():
            raise ValidationError(f"{self.store.name} does not accept payment in {self.currency}")

    def issue_voucher(self, **data):
        data.update(
            {
                "iat": datetime.datetime.utcnow(),
                "iss": self.external_identifier,
                "checkout_id": str(self.id),
                "token": {"symbol": self.currency.code, "address": self.currency.address},
                "payments": [
                    {
                        "id": str(p.id),
                        "amount": str(p.amount),
                        "confirmed": p.is_confirmed,
                        "identifier": p.identifier,
                        "route": p.route.get_route_name(),
                    }
                    for p in self.payments
                ],
                "total_amount": str(self.amount),
                "total_confirmed": str(self.total_confirmed),
                "is_paid": self.is_paid,
                "is_confirmed": self.is_confirmed,
            }
        )

        private_key = self.store.rsa.private_key_pem.encode()
        return jwt.encode(data, private_key, algorithm="RS256").decode()


__all__ = ["Store", "StoreRSAKeyPair", "Checkout"]
