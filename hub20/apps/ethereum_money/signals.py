from django.dispatch import Signal

account_deposit_received = Signal(providing_args=["account", "transaction", "amount"])
blockchain_payment_sent = Signal(providing_args=["recipient", "amount", "transaction_hash"])

__all__ = [
    "account_deposit_received",
    "blockchain_payment_sent",
]
