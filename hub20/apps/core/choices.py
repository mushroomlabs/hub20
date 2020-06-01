from model_utils import Choices

PAYMENT_ORDER_STATUS = Choices("open", "paid", "confirmed", "expired")
TRANSFER_EVENT_TYPES = Choices("scheduled", "failed", "canceled", "executed", "confirmed")
PAYMENT_METHODS = Choices("blockchain", "raiden", "internal")
