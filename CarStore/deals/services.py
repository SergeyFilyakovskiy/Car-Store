from decimal import Decimal

from accounts.models import Buyer
from core.enums import StatusEnum
from dealers.models import Dealership, DealershipInventory, DealershipPromo
from django.db import transaction
from django.utils import timezone

from deals.models import Offer, PurchaseHistory, Transaction

from .dto import DealResult
from .exceptions import InsufficientBalanceError, OutOfStockError


def calculate_final_price(offer: Offer, inventory: DealershipInventory) -> Decimal:
    """
    Calculates the final transaction price.

    Rule: the buyer pays the MINIMUM of (max_price, sale_price),
    minus active discounts.
    """

    base_price = min(offer.max_price, inventory.sale_price)

    active_promo = (
        DealershipPromo.objects.filter(
            dealer=inventory.dealer_id,
            promo_active__car_model=offer.car_model,
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date(),
        )
        .order_by("-discount_pct")
        .first()
    )

    if active_promo:
        discount = base_price * active_promo.discount_pct / Decimal("100")
        final_price = base_price - discount
    else:
        final_price = base_price

    return final_price


@transaction.atomic
def accept_offer(offer: Offer, dealership: Dealership) -> DealResult:
    buyer = Buyer.objects.select_for_update().get(id=Offer.buyer)
    inventory = DealershipInventory.objects.select_for_update().get(
        dealer_id=dealership.id, car_model_id=offer.car_model
    )

    if inventory.quantity <= 0:
        raise OutOfStockError("Dealership doesn't have enough cars in stock.")

    final_price = calculate_final_price(offer, inventory)

    if buyer.balance < final_price:
        raise InsufficientBalanceError(
            f"Need {final_price}, but buyer has {buyer.balance}"
        )

    buyer.balance -= final_price
    buyer.save()

    inventory.quantity -= 1
    inventory.save()

    offer.accepted_price = final_price
    offer.status = StatusEnum.COMPLETED
    offer.save()

    transaction = Transaction.objects.create(
        transaction_type=Transaction.TransactionType.SALE,
        amount=final_price,
        buyer=buyer,
        dealership=dealership,
        car_model=offer.car_model,
        offer=offer,
    )

    history = PurchaseHistory.objects.create(
        buyer=buyer,
        dealership=dealership,
        car_model=offer.car_model,
        offer=offer,
        transaction=transaction,
        price_paid=final_price,
    )

    return DealResult(
        offer=offer,
        transaction=transaction,
        purchase_history=history,
        updated_buyer_balance=buyer.balance,
        updated_inventory_quantity=inventory.quantity,
        final_price=final_price,
    )
