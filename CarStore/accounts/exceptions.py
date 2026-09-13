class BalanceTopUpError(Exception):
    """Base exception for balance top-up service."""


class TopUpAlreadyProcessedErorr(BalanceTopUpError):
    pass


class TopUpInvalidStatusError(BalanceTopUpError):
    pass
