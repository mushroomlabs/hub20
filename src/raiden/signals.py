from django.dispatch import Signal

raiden_payment_received = Signal(providing_args=["payment"])
