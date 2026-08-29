from dataclasses import dataclass
from decimal import Decimal

from .models import Offer, PurchaseHistory, Transaction


@dataclass(frozen=True)
class DealsResult:
    offer: Offer
    transaction: Transaction
    purchase_history: PurchaseHistory
    updated_user_balance: Decimal
