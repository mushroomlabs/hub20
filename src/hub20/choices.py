from model_utils import Choices

PAYMENT_STATUS = Choices("requested", "partial", "received", "confirmed", "expired", "voided")
