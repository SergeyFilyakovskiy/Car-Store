"""
A pricing service for calculating effective supplier prices.

Effective price = supplier base price
                  - active promotion discount
                  - loyalty discount

Discounts are additive (percentages are summed), but the total cannot exceed 90%.

"Discount outlook" refers to the best price that will be in effect
when the next scheduled promotion within the planning horizon begins.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from cars.models import CarModel
from deals.models import SupplyHistory
from django.utils import timezone
from suppliers.models import (
    Supplier,
    SupplierCar,
    SupplierLoyaltyDiscount,
    SupplierPromoModel,
)

from dealers.models import Dealership

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
MAX_TOTAL_DISCOUNT_PCT = Decimal("90")
FUTURE_PROMO_HORIZON_DAYS = 30


@dataclass
class SupplyQuote:
    """Result of the calculation of the supplier's effective price for the showroom model."""

    supplier: Supplier
    car_model: CarModel
    base_price: Decimal
    stock_quantity: int
    promo_discount_pct: Decimal
    loyalty_discount_pct: Decimal
    total_discount_pct: Decimal
    final_price: Decimal
    promo_id: Any | None = None
    future_promo_discount_pct: Decimal | None = None
    future_best_price: Decimal | None = None
    future_best_price_date: date | None = None
    reason: str = ""

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0


def _quantize(value: Decimal) -> Decimal:
    """Rounding to the nearest cent."""
    return value.quantize(CENT)


def apply_discount(base_price: Decimal, total_pct: Decimal) -> Decimal:
    """Applies the total discount percentage to the base price."""
    if total_pct <= 0:
        return _quantize(base_price)
    discount = base_price * total_pct / HUNDRED
    return _quantize(base_price - discount)


def get_active_promo_discount(
    supplier: Supplier,
    car_model: CarModel,
    on_date: date | None = None,
) -> tuple[Decimal, object | None]:
    """
    The best active supplier promotion for the model on a given date.

    Returns (discount_pct, promo_id). If there are no promotions, returns (0, None).
    """
    if on_date is None:
        on_date = timezone.now().date()

    link = (
        SupplierPromoModel.objects.filter(
            is_active=True,
            car_model=car_model,
            promo__is_active=True,
            promo__supplier=supplier,
            promo__start_date__lte=on_date,
            promo__end_date__gte=on_date,
        )
        .select_related("promo")
        .order_by("-promo__discount_pct")
        .first()
    )

    if link is None:
        return Decimal("0"), None
    return link.promo.discount_pct, link.promo.id


def get_future_promo_discount(
    supplier: Supplier,
    car_model: CarModel,
    on_date: date | None = None,
    horizon_days: int = FUTURE_PROMO_HORIZON_DAYS,
) -> tuple[Decimal, object | None, date | None]:
    """
    The best upcoming promotion starting within the time horizon.

    Returns (discount_pct, promo_id, start_date).
    If there are no upcoming promotions — (0, None, None).
    """
    if on_date is None:
        on_date = timezone.now().date()
    horizon_end = on_date + timedelta(days=horizon_days)

    links = SupplierPromoModel.objects.filter(
        is_active=True,
        car_model=car_model,
        promo__is_active=True,
        promo__supplier=supplier,
        promo__start_date__gt=on_date,
        promo__start_date__lte=horizon_end,
    ).select_related("promo")

    best = max(links, key=lambda link: link.promo.discount_pct, default=None)

    if best is None:
        return Decimal("0"), None, None
    return best.promo.discount_pct, best.promo.id, best.promo.start_date


def get_loyalty_discount(supplier: Supplier, dealership: Dealership) -> Decimal:
    """
    Loyalty discount based on the number of purchases a salon makes from the supplier.

    Uses SupplyHistory as the source of truth for calculating purchases.
    If the number of purchases is less than min_purchases, the discount is not applied.
    """
    purchases_count = SupplyHistory.objects.filter(
        dealership=dealership,
        supplier=supplier,
    ).count()

    discount = (
        SupplierLoyaltyDiscount.objects.filter(
            is_active=True,
            supplier=supplier,
            dealer=dealership,
        )
        .order_by("-min_purchases")
        .first()
    )

    if discount is None:
        return Decimal("0")

    if purchases_count < discount.min_purchases:
        return Decimal("0")

    return discount.discount_pct


def get_supply_quote(
    supplier: Supplier,
    car_model: CarModel,
    dealership: Dealership,
    now: datetime | None = None,
) -> SupplyQuote:
    """
    A comprehensive calculation of the effective supplier price for a specific model at the dealership.

    Takes into account:
      - base price (SupplierCar.base_price)
      - active promotions (as of today)
      - loyalty (based on purchase volume from SupplyHistory)
      - discount prospects (future promotions within the planning horizon)
    """
    if now is None:
        now = timezone.now()
    today = now.date()

    supplier_car = SupplierCar.objects.filter(
        is_active=True,
        supplier=supplier,
        car_model=car_model,
    ).first()

    if supplier_car is None:
        return SupplyQuote(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("0"),
            stock_quantity=0,
            promo_discount_pct=Decimal("0"),
            loyalty_discount_pct=Decimal("0"),
            total_discount_pct=Decimal("0"),
            final_price=Decimal("0"),
            reason="no_supplier_car",
        )

    base_price = supplier_car.base_price

    promo_pct, promo_id = get_active_promo_discount(supplier, car_model, today)

    loyalty_pct = get_loyalty_discount(supplier, dealership)

    total_pct = min(promo_pct + loyalty_pct, MAX_TOTAL_DISCOUNT_PCT)
    final_price = apply_discount(base_price, total_pct)

    future_pct, future_promo_id, future_start_date = get_future_promo_discount(
        supplier, car_model, today
    )

    future_best_price = None
    future_best_price_date = None
    if future_pct > 0:
        future_total_pct = min(future_pct + loyalty_pct, MAX_TOTAL_DISCOUNT_PCT)
        future_best_price = apply_discount(base_price, future_total_pct)
        future_best_price_date = future_start_date

    reason = _build_reason(promo_pct, loyalty_pct)

    return SupplyQuote(
        supplier=supplier,
        car_model=car_model,
        base_price=base_price,
        stock_quantity=supplier_car.stock_quantity,
        promo_discount_pct=promo_pct,
        loyalty_discount_pct=loyalty_pct,
        total_discount_pct=total_pct,
        final_price=final_price,
        promo_id=promo_id,
        future_promo_discount_pct=future_pct if future_pct > 0 else None,
        future_best_price=future_best_price,
        future_best_price_date=future_best_price_date,
        reason=reason,
    )


def _build_reason(promo_pct: Decimal, loyalty_pct: Decimal) -> str:
    """Human-readable reason for the final price in the logs."""
    parts = []
    if promo_pct > 0:
        parts.append(f"promo_{promo_pct}%")
    if loyalty_pct > 0:
        parts.append(f"loyalty_{loyalty_pct}%")
    if not parts:
        return "base_price"
    return "base_price+" + "+".join(parts)
