from django.dispatch import Signal

incoming_transfer_broadcast = Signal(providing_args=["account", "chain_id", "transaction_data"])
incoming_transfer_mined = Signal(providing_args=["account", "chain_id", "transaction"])
outgoing_transfer_broadcast = Signal(providing_args=["account", "chain_id", "transaction_data"])
outgoing_transfer_mined = Signal(providing_args=["account", "chain_id", "transaction"])


account_deposit_received = Signal(providing_args=["account", "transaction", "amount"])
blockchain_payment_sent = Signal(providing_args=["recipient", "amount", "transaction_hash"])

__all__ = [
    "incoming_transfer_broadcast",
    "incoming_transfer_mined",
    "outgoing_transfer_broadcast",
    "outgoing_transfer_mined",
    "account_deposit_received",
    "blockchain_payment_sent",
]
