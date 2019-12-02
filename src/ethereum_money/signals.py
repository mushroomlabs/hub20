from django.dispatch import Signal

account_deposit_received = Signal(providing_args=["account", "transaction", "amount"])
