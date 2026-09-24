class BalanceTopUpError(Exception):
    """Base exception for balance top-up service."""


class TopUpAlreadyProcessedError(BalanceTopUpError):
    pass


class TopUpInvalidStatusError(BalanceTopUpError):
    pass


class InsufficientBalanceError(Exception):
    """Buyer doesn't have enough balance."""

    pass
