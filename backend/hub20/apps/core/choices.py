from model_utils import Choices

DEPOSIT_STATUS = Choices("open", "paid", "confirmed", "expired")
TRANSFER_STATUS = Choices("scheduled", "processed", "failed", "canceled", "executed")
PAYMENT_NETWORKS = Choices("blockchain", "raiden", "internal")
