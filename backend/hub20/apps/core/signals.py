from django.dispatch import Signal

order_canceled = Signal(providing_args=["order", "request"])
payment_received = Signal(providing_args=["payment"])
transfer_scheduled = Signal(providing_args=["transfer"])
transfer_confirmed = Signal(providing_args=["transfer"])
transfer_executed = Signal(providing_args=["transfer"])
transfer_failed = Signal(providing_args=["transfer", "reason"])

__all__ = [
    "order_canceled",
    "payment_received",
    "transfer_scheduled",
    "transfer_confirmed",
    "transfer_executed",
    "transfer_failed",
]
