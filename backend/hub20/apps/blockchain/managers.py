from django.db import models
from django.db.models import Max, Q


class TransactionManager(models.Manager):
    def involving_address(self, chain, address):
        return self.filter(block__chain=chain).filter(
            Q(from_address=address) | Q(to_address=address)
        )

    def last_block_with(self, chain, address):
        qs = self.involving_address(chain, address).select_related("block")
        return qs.aggregate(highest=Max("block__number")).get("highest") or 0
