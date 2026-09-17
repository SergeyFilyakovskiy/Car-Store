from decimal import Decimal

from accounts.models import LedgerEntry, User
from accounts.services import BalanceService
from core.enums import StatusEnum
from dealers.models import Dealership, DealershipInventory, DealershipPromo
from django.db import transaction
from django.utils import timezone

from deals.models import Offer, PurchaseHistory, Transaction

from .dto import DealResult
from .exceptions import (
    InsufficientBalanceError,
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OutOfStockError,
)


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
            promo_models__car_model=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
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

    return final_price.quantize(Decimal("0.01"))


@transaction.atomic
def accept_offer(offer: Offer, dealership: Dealership) -> DealResult:
    """
    Accepts an offer and creates a deal.

    Raises:
        OfferAlreadyProcessedError: if the offer has already been processed
        OfferExpiredError: if the offer has expired
        InsufficientBalanceError: if the buyer lacks funds
        OutOfStockError: if there are no cars in stock
    """
    if offer.status != StatusEnum.PENDING:
        raise OfferAlreadyProcessedError(
            f"Offer {offer.id} already processed (status: {offer.status})"
        )

    if offer.expires_at < timezone.now():
        raise OfferExpiredError(f"Offer {offer.id} expired at {offer.expires_at}")

    # 1. Lock both users in ONE query (deterministic order -> no deadlocks)
    buyer_user_id = offer.buyer.user_id
    dealer_user_id = dealership.account_id_id  # pyright: ignore[reportAttributeAccessIssue]
    locked_users = {
        user.id: user
        for user in User.objects.select_for_update().filter(
            id__in=[buyer_user_id, dealer_user_id]
        )
    }
    buyer_user = locked_users[buyer_user_id]
    dealer_user = locked_users[dealer_user_id]

    # 2. Buyer profile is already loaded on the offer instance - no extra query
    buyer_profile = offer.buyer

    # 3. Lock the inventory row
    inventory = DealershipInventory.objects.select_for_update().get(
        dealer_id=dealership.id,
        car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
    )

    if inventory.quantity <= 0:
        raise OutOfStockError("Dealership doesn't have enough cars in stock.")

    final_price = calculate_final_price(offer, inventory)

    if buyer_user.balance < final_price:
        raise InsufficientBalanceError(
            f"Need {final_price}, but buyer has {buyer_user.balance}"
        )

    # 4. Create the deal record FIRST, so ledger entries can reference it
    deal_transaction = Transaction.objects.create(
        transaction_type=Transaction.TransactionType.SALE,
        amount=final_price,
        buyer=buyer_profile,
        dealership=dealership,
        car_model=offer.car_model,
        offer=offer,
    )

    # 5. Move money via BalanceService (writes ledger entries atomically)
    BalanceService.debit(
        user=buyer_user,
        amount=final_price,
        entry_type=LedgerEntry.EntryType.PURCHASE,
        description=f"Car purchase: {offer.car_model.name}",
        deal_transaction=deal_transaction,
    )
    BalanceService.credit(
        user=dealer_user,
        amount=final_price,
        entry_type=LedgerEntry.EntryType.SALE,
        description=f"Car sale: {offer.car_model.name}",
        deal_transaction=deal_transaction,
    )

    # 6. Decrease stock
    inventory.quantity -= 1
    inventory.save(update_fields=["quantity"])

    # 7. Record purchase history
    history = PurchaseHistory.objects.create(
        buyer=buyer_profile,
        dealership=dealership,
        car_model=offer.car_model,
        offer=offer,
        transaction=deal_transaction,
        price_paid=final_price,
        cost_price=inventory.purchase_price,
    )

    # 8. Finalize the offer
    offer.accepted_price = final_price
    offer.status = StatusEnum.COMPLETED
    offer.save(update_fields=["accepted_price", "status"])

    return DealResult(
        offer=offer,
        transaction=deal_transaction,
        purchase_history=history,
        updated_buyer_balance=buyer_user.balance,
        updated_inventory_quantity=inventory.quantity,
        final_price=final_price,
    )
