from django.dispatch import Signal

transfer_received = Signal(providing_args=["transfer"])
transfer_confirmed = Signal(providing_args=["transfer"])
payment_confirmed = Signal(providing_args=["payment"])


__all__ = ["transfer_received", "transfer_confirmed", "payment_confirmed"]
