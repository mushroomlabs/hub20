import datetime
from typing import Optional

from django.db import models
from django.db.models import ExpressionWrapper, F
from django.db.models.functions import Lower, Upper
from django.utils import timezone


class BlockchainRouteManager(models.Manager):
    def with_expiration(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.annotate(
            start_block=Lower("payment_window"), expiration_block=Upper("payment_window")
        )

    def expired(self, block_number: Optional[int] = None) -> models.QuerySet:
        qs = self.with_expiration()

        at_block = block_number if block_number is not None else F("order__chain__highest_block")
        return qs.filter(expiration_block__lt=at_block)

    def available(self, block_number: Optional[int] = None) -> models.QuerySet:
        qs = self.with_expiration()
        at_block = block_number if block_number is not None else F("order__chain__highest_block")

        return qs.filter(start_block__lte=at_block, expiration_block__gte=at_block)


class RaidenRouteManager(models.Manager):
    def with_expiration(self) -> models.QuerySet:
        qs = super().get_queryset()
        return qs.annotate(
            expiration_time=ExpressionWrapper(
                F("created") + F("payment_window"), output_field=models.DateTimeField()
            )
        )

    def expired(self, at: Optional[datetime.datetime] = None) -> models.QuerySet:
        date_value = at or timezone.now()
        return self.with_expiration().filter(expiration_time__lt=date_value)

    def available(self, at: Optional[datetime.datetime] = None) -> models.QuerySet:
        date_value = at or timezone.now()
        return self.with_expiration().filter(
            created__lte=date_value, expiration_time__gte=date_value
        )


__all__ = ["BlockchainRouteManager", "RaidenRouteManager"]
