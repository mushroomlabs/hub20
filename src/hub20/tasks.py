import logging

from celery import shared_task

from . import models

logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    transfer = models.Transfer.objects.get_subclass(id=transfer_id)
    transfer.execute()
