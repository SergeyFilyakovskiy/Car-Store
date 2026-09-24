from dataclasses import dataclass
from decimal import Decimal

from accounts.models import Transaction
from dealers.models import DealershipInventory

from .models import Offer, PurchaseHistory


@dataclass(frozen=True)
class DealResult:
    """Result of a buyer -> dealership deal."""

    offer: Offer
    transaction: Transaction
    purchase_history: PurchaseHistory
    unit_price: Decimal
    total_price: Decimal
    quantity: int


@dataclass(frozen=True)
class SupplyResult:
    """Result of a dealership -> supplier stock purchase."""

    offer: Offer
    transaction: Transaction
    inventory: DealershipInventory
    unit_price: Decimal
    total_price: Decimal
    quantity: int
