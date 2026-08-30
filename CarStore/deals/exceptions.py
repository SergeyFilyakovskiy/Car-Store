class DealError(Exception):
    """Base exception for deal opertions."""

    pass


class OfferAlreadyProcessedError(DealError):
    """Offer status is not PENDING"""

    pass


class OfferExpiredError(DealError):
    """Offer has expired."""

    pass


class InsufficientBalanceError(DealError):
    """Buyer doesn't have enough balance."""

    pass


class OutOfStockError(DealError):
    """Dealership has no cars of this model in stock."""

    pass


class PriceMismatchError(DealError):
    """Offer max_price is less than inventory sale_price."""

    pass
