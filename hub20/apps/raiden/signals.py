from django.dispatch import Signal

raiden_payment_received = Signal(providing_args=["payment"])
raiden_payment_sent = Signal(providing_args=["payment"])
service_deposit_sent = Signal(providing_args=["transaction", "raiden", "amount"])
