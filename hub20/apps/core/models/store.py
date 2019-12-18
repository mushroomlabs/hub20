import base64
import datetime
import secrets
import uuid
from typing import Optional

import jwt
from Crypto.PublicKey import RSA
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import HttpRequest
from model_utils.models import TimeStampedModel

from hub20.apps.core.app_settings import API_KEY_HEADER_NAME
from hub20.apps.ethereum_money.models import EthereumToken

from .payments import PaymentOrder


class StoreQuerySet(models.QuerySet):
    def accessible_to(self, request: HttpRequest):
        access_q = Q(api__key=StoreAPIKey.get_decoded_key(request))
        if request.user.is_authenticated:
            access_q |= Q(owner=request.user)
        return self.filter(access_q)


class Store(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=300)
    url = models.URLField()
    accepted_currencies = models.ManyToManyField(EthereumToken)

    objects = StoreQuerySet.as_manager()

    @property
    def api_key(self):
        return self.api and base64.b64encode(self.api.key).decode()


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


class StoreAPIKey(models.Model):
    DEFAULT_KEY_SIZE = 32

    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name="api")
    key = models.BinaryField()

    @classmethod
    def generate(cls, store, keysize: Optional[int] = None):
        key = secrets.token_bytes(keysize)
        api_key, _ = cls.objects.update_or_create(store=store, defaults={"key": key})
        return api_key

    @staticmethod
    def get_decoded_key(request: HttpRequest) -> Optional[bytes]:
        def get_from_authz():
            authorization = request.META.get("HTTP_AUTHORIZATION")

            if not authorization:
                return None

            try:
                _, key = authorization.split("Api-Key ")
                return key
            except ValueError:
                return None

        def get_from_header():
            return request.META.get(API_KEY_HEADER_NAME) or None

        key = get_from_authz() or get_from_header()

        if key is None:
            return None

        return base64.b64decode(key)


class Checkout(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)
    external_identifier = models.TextField()
    requester_ip = models.GenericIPAddressField(null=True)

    def clean(self):
        if self.store.owner != self.payment_order.user:
            raise ValidationError("Creator or payment order must be the same as store owner")

        if self.payment_order.currency not in self.store.accepted_currencies.all():
            raise ValidationError(
                f"{self.store.name} does not accept payment in {self.payment_order.currency}"
            )

    def issue_voucher(self, **data):
        data.update(
            {
                "iat": datetime.datetime.utcnow(),
                "iss": self.external_identifier,
                "status": self.payment_order.status,
                "currency": self.payment_order.currency.ticker,
                "total_amount": str(self.payment_order.amount),
                "total_confirmed": str(self.payment_order.total_confirmed),
                "payment_order_id": self.payment_order.id,
                "checkout_id": str(self.id),
            }
        )

        private_key = self.store.rsa.private_key_pem.encode()
        return jwt.encode(data, private_key, algorithm="RS256").decode()


__all__ = ["Store", "StoreRSAKeyPair", "StoreAPIKey", "Checkout"]
