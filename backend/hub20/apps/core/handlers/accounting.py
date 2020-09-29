import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.core.models import (
    PaymentConfirmation,
    TransferConfirmation,
    TransferExecution,
    UserAccount,
)

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def on_user_created_create_account(sender, **kw):
    if kw["created"]:
        UserAccount.objects.get_or_create(user=kw["instance"])


@receiver(post_save, sender=PaymentConfirmation)
def on_payment_confirmed_set_user_credit(sender, **kw):
    if kw["created"]:
        confirmation = kw["instance"]
        payment = confirmation.payment

        user = payment.route.order.user
        book, _ = user.account.books.get_or_create(token=payment.currency)

        book.credits.create(
            reference=confirmation, amount=payment.amount, currency=payment.currency
        )


@receiver(post_save, sender=TransferExecution)
def on_transfer_executed_deduct_sender_balance(sender, **kw):
    if kw["created"]:
        execution = kw["instance"]
        transfer = execution.transfer
        book, _ = transfer.sender.account.books.get_or_create(token=transfer.currency)
        book.debits.create(reference=execution, currency=transfer.currency, amount=transfer.amount)


@receiver(post_save, sender=TransferConfirmation)
def on_internal_transfer_confirmed_credit_receiver(sender, **kw):
    if kw["created"]:
        confirmation = kw["instance"]

        transfer = confirmation.transfer

        if hasattr(transfer, "internaltransfer"):
            receiver = transfer.internaltransfer.receiver
            book, _ = receiver.account.books.get_or_create(token=transfer.currency)
            book.credits.create(
                reference=confirmation, currency=transfer.currency, amount=transfer.amount
            )


__all__ = [
    "on_payment_confirmed_set_user_credit",
    "on_user_created_create_account",
    "on_transfer_executed_deduct_sender_balance",
    "on_internal_transfer_confirmed_credit_receiver",
]
