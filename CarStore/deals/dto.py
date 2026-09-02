from dataclasses import dataclass
from decimal import Decimal

from .models import Offer, PurchaseHistory, Transaction


@dataclass(frozen=True)
class DealResult:
    offer: Offer
    transaction: Transaction
    purchase_history: PurchaseHistory
    updated_buyer_balance: Decimal
    updated_inventory_quantity: int
    final_price: Decimal
