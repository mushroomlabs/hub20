from django.dispatch import Signal

blockchain_payment_sent = Signal(providing_args=["recipient", "amount", "transaction_data"])
payment_received = Signal(providing_args=["payment"])
payment_confirmed = Signal(providing_args=["payment"])
order_paid = Signal(providing_args=["payment_order"])
transfer_scheduled = Signal(providing_args=["transfer"])
transfer_confirmed = Signal(providing_args=["transfer"])
transfer_executed = Signal(providing_args=["transfer"])
transfer_failed = Signal(providing_args=["transfer", "reason"])

__all__ = [
    "blockchain_payment_sent",
    "payment_received",
    "payment_confirmed",
    "order_paid",
    "transfer_scheduled",
    "transfer_confirmed",
    "transfer_executed",
    "transfer_failed",
]
