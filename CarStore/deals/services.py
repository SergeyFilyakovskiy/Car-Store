"""
Deal services.

Two flows share the same pipeline:
    validate offer -> lock stock -> price the unit -> move money
    (accounts.MoneyService) -> update stock -> record the deal.

    - accept_purchase_offer: buyer's offer is accepted by a dealership
    - accept_supply_offer:   dealership's offer is accepted by a supplier
"""

from decimal import Decimal

from accounts.services import MoneyService
from core.enums import StatusEnum
from dealers.models import (
    Dealership,
    DealershipInventory,
    DealershipPromoModel,
)
from django.db import transaction
from django.utils import timezone
from suppliers.models import Supplier, SupplierCar, SupplierPromoModel

from deals.models import Offer, PurchaseHistory

from .dto import DealResult, SupplyResult
from .exceptions import (
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OfferRoleError,
    OutOfStockError,
)

CENT = Decimal("0.01")


# ---------------------------------------------------------------------------
# Validation & pricing helpers
# ---------------------------------------------------------------------------


def _validate_offer(offer: Offer, expected_creator_role: str) -> None:
    """Common offer checks for both flows."""
    if offer.status != StatusEnum.PENDING:
        raise OfferAlreadyProcessedError(
            f"Offer {offer.id} already processed (status: {offer.status})"
        )

    if offer.expires_at < timezone.now():
        raise OfferExpiredError(f"Offer {offer.id} expired at {offer.expires_at}")

    if offer.creator.role != expected_creator_role:
        raise OfferRoleError(
            f"Offer {offer.id} created by role '{offer.creator.role}', "
            f"expected '{expected_creator_role}'"
        )


def _best_promo_discount(promo_model_qs) -> Decimal:
    """Returns the highest active discount percent among the given promo links."""
    link = (
        promo_model_qs.select_related("promo").order_by("-promo__discount_pct").first()
    )
    return link.promo.discount_pct if link else Decimal("0")


def _unit_price_with_discount(base_unit: Decimal, discount_pct: Decimal) -> Decimal:
    """Applies a percent discount to a unit price and rounds to cents."""
    if discount_pct <= 0:
        return base_unit.quantize(CENT)
    discount = base_unit * discount_pct / Decimal("100")
    return (base_unit - discount).quantize(CENT)


def calculate_purchase_unit_price(
    offer: Offer, inventory: DealershipInventory
) -> Decimal:
    """
    Unit price for a buyer -> dealership deal.

    Rule: MIN(offer.max_price, inventory.sale_price) minus the best
    active dealership promo for this car model.
    """
    base_unit = min(offer.max_price, inventory.sale_price)
    today = timezone.now().date()

    discount = _best_promo_discount(
        DealershipPromoModel.objects.filter(
            car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
            promo__dealer=inventory.dealer_id,
            promo__start_date__lte=today,
            promo__end_date__gte=today,
        )
    )
    return _unit_price_with_discount(base_unit, discount)


def calculate_supply_unit_price(offer: Offer, supplier_car: SupplierCar) -> Decimal:
    """
    Unit price for a dealership -> supplier deal.

    Rule: MIN(offer.max_price, supplier_car.base_price) minus the best
    active supplier promo for this car model.
    """
    base_unit = min(offer.max_price, supplier_car.base_price)
    today = timezone.now().date()

    discount = _best_promo_discount(
        SupplierPromoModel.objects.filter(
            car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
            promo__supplier=supplier_car.supplier_id,  # pyright: ignore[reportAttributeAccessIssue]
            promo__start_date__lte=today,
            promo__end_date__gte=today,
        )
    )
    return _unit_price_with_discount(base_unit, discount)


# ---------------------------------------------------------------------------
# Flow 1: buyer -> dealership
# ---------------------------------------------------------------------------


@transaction.atomic
def accept_purchase_offer(offer: Offer, dealership: Dealership) -> DealResult:
    """
    Dealership accepts a buyer's offer.

    Raises:
        OfferAlreadyProcessedError: offer is not PENDING
        OfferExpiredError: offer has expired
        OfferRoleError: offer was not created by a buyer
        OutOfStockError: dealership has not enough cars in stock
        InsufficientBalanceError: buyer lacks funds (raised by MoneyService)
    """
    _validate_offer(offer, expected_creator_role="buyer")

    # Lock the stock row first (consistent lock order: stock -> users)
    inventory = DealershipInventory.objects.select_for_update().get(
        dealer_id=dealership.id,
        car_model_id=offer.car_model_id,  # type: ignore
    )

    if inventory.quantity < offer.quantity:
        raise OutOfStockError(
            f"Need {offer.quantity}, but only {inventory.quantity} in stock"
        )

    unit_price = calculate_purchase_unit_price(offer, inventory)
    total_price = (unit_price * offer.quantity).quantize(CENT)

    # Money moves through the ledger; idempotency key is tied to the offer
    deal = MoneyService.transfer(
        from_user_id=offer.creator_id,  # type: ignore
        to_user_id=dealership.account_id_id,  # type: ignore
        amount=total_price,
        idempotency_key=f"offer-{offer.id}",
        description=f"Car purchase: {offer.car_model.name} x{offer.quantity}",
    )

    inventory.quantity -= offer.quantity
    inventory.save(update_fields=["quantity"])

    # Both prices are stored as LOT totals, so Sum() in stats stays correct
    history = PurchaseHistory.objects.create(
        buyer=offer.creator.buyer,
        dealership=dealership,
        car_model=offer.car_model,
        offer=offer,
        transaction=deal,
        price_paid=total_price,
        cost_price=(inventory.purchase_price * offer.quantity).quantize(CENT),
        quantity=offer.quantity,
    )

    offer.status = StatusEnum.COMPLETED
    offer.save(update_fields=["status"])

    return DealResult(
        offer=offer,
        transaction=deal,
        purchase_history=history,
        unit_price=unit_price,
        total_price=total_price,
        quantity=offer.quantity,
    )


# ---------------------------------------------------------------------------
# Flow 2: dealership -> supplier
# ---------------------------------------------------------------------------


@transaction.atomic
def accept_supply_offer(offer: Offer, supplier: Supplier) -> SupplyResult:
    """
    Supplier accepts a dealership's purchase offer.

    Raises:
        OfferAlreadyProcessedError: offer is not PENDING
        OfferExpiredError: offer has expired
        OfferRoleError: offer was not created by a dealership
        OutOfStockError: supplier has not enough cars in stock
        InsufficientBalanceError: dealership lacks funds (raised by MoneyService)
    """
    _validate_offer(offer, expected_creator_role="dealership")

    # Lock the supplier's stock row
    supplier_car = SupplierCar.objects.select_for_update().get(
        supplier_id=supplier.id,
        car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
    )

    if supplier_car.stock_quantity < offer.quantity:
        raise OutOfStockError(
            f"Need {offer.quantity}, but only {supplier_car.stock_quantity} "
            f"at {supplier.name}"
        )

    # The buying dealership is the offer creator's own dealership
    dealership = Dealership.objects.select_for_update().get(
        account_id=offer.creator_id  # pyright: ignore[reportAttributeAccessIssue]
    )

    # Lock the inventory row (may not exist yet - first purchase of this model)
    inventory = (
        DealershipInventory.objects.select_for_update()
        .filter(
            dealer_id=dealership.id,
            car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
        )
        .first()
    )

    unit_price = calculate_supply_unit_price(offer, supplier_car)
    total_price = (unit_price * offer.quantity).quantize(CENT)

    deal = MoneyService.transfer(
        from_user_id=offer.creator_id,  # pyright: ignore[reportAttributeAccessIssue]
        to_user_id=supplier.account_id_id,  # pyright: ignore[reportAttributeAccessIssue]
        amount=total_price,
        idempotency_key=f"offer-{offer.id}",
        description=f"Stock purchase: {offer.car_model.name} x{offer.quantity}",
    )

    supplier_car.stock_quantity -= offer.quantity
    supplier_car.save(update_fields=["stock_quantity"])

    if inventory is None:
        # First purchase of this model: sale_price starts at cost,
        # the dealership will adjust it later
        inventory = DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=offer.car_model_id,  # pyright: ignore[reportAttributeAccessIssue]
            quantity=offer.quantity,
            purchase_price=unit_price,
            sale_price=unit_price,
        )
    else:
        inventory.quantity += offer.quantity
        inventory.purchase_price = unit_price
        inventory.save(update_fields=["quantity", "purchase_price"])

    offer.status = StatusEnum.COMPLETED
    offer.save(update_fields=["status"])

    return SupplyResult(
        offer=offer,
        transaction=deal,
        inventory=inventory,
        unit_price=unit_price,
        total_price=total_price,
        quantity=offer.quantity,
    )
