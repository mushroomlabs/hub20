class RaidenOperationError(Exception):
    pass


class RaidenMissingPrecondition(Exception):
    pass


class RaidenConnectionError(Exception):
    pass


class RaidenPaymentError(Exception):
    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message

    def __str__(self):
        return f"Payment Error: {self.message} ({self.error_code})"
