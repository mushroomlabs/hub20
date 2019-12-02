from model_utils import Choices

PAYMENT_EVENT_TYPES = Choices("requested", "partial", "received", "confirmed", "expired", "voided")
TRANSFER_EVENT_TYPES = Choices("scheduled", "failed", "canceled", "executed", "confirmed")
