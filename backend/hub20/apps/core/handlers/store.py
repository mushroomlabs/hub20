import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.core.models import Store, StoreRSAKeyPair

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Store)
def on_store_created_generate_key_pair(sender, **kw):
    store = kw["instance"]
    if kw["created"]:
        StoreRSAKeyPair.generate(store)


__all__ = [
    "on_store_created_generate_key_pair",
]
