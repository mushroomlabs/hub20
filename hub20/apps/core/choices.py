from model_utils import Choices

PAYMENT_EVENT_TYPES = Choices(
    "requested", "partial", "received", "confirmed", "expired", "canceled", "voided"
)
TRANSFER_EVENT_TYPES = Choices("scheduled", "failed", "canceled", "executed", "confirmed")
PAYMENT_METHODS = Choices("blockchain", "raiden", "internal")
