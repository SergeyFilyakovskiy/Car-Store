"""
Service for purchasing vehicles from suppliers.

Used in Task 1 (runs every 10 minutes).

Process:
1. Pass 1 (preferred): purchase models matching the dealership's preferences
2. Pass 2 (demand): purchase based on demand (sales over 30 days / 30)

Coverage thresholds:
- ≤ 2 days: purchase
- ≥ 14 days: do not purchase
- In between: do not purchase (safe for the balance)

Idempotency is ensured via `PurchasePlan` using a unique key
based on the time slot (rounded to the nearest 10 minutes).
"""

import math
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any

from cars.models import CarModel
from deals.exceptions import (
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OfferRoleError,
    OutOfStockError,
)
from deals.models import Offer, SupplyHistory
from deals.services import accept_supply_offer
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from dealers.models import (
    Dealership,
    DealershipInventory,
    DealershipPreference,
    DealershipSupplier,
    PurchaseLog,
    PurchasePlan,
)

BUY_BELOW_DAYS = Decimal("2")
NO_BUY_ABOVE_DAYS = Decimal("14")
TARGET_COVERAGE_DAYS = Decimal("14")
SLOT_MINUTES = 10


def floor_to_interval(dt: Any, minutes: int = SLOT_MINUTES) -> Any:
    """Rounds the datetime down to the nearest interval."""
    return dt.replace(
        minute=(dt.minute // minutes) * minutes,
        second=0,
        microsecond=0,
    )


class PurchaseService:
    """A service for the automated purchasing of vehicles."""

    def execute(self, dealership: Dealership, run_id: uuid.UUID) -> dict[str, Any]:
        """
        Initiates the purchasing process for a single dealership.

        Args:
            dealership: The dealership for which the purchase is being performed
            run_id: UUID for grouping logs

        Returns:
            A dictionary containing statistics: the number of plans, purchases, and rejections
        """
        stats = {
            "dealership_id": str(dealership.id),
            "preferred_plans": 0,
            "demand_plans": 0,
            "purchases": 0,
            "rejections": 0,
        }

        now = timezone.now()

        with transaction.atomic():
            preferred_stats = self._process_preferred_pass(
                dealership=dealership, run_id=run_id, now=now
            )
            stats["preferred_plans"] = preferred_stats["plans_created"]
            stats["purchases"] += preferred_stats["purchases"]
            stats["rejections"] += preferred_stats["rejections"]

            demand_stats = self._process_demand_pass(
                dealership=dealership, run_id=run_id, now=now
            )
            stats["demand_plans"] = demand_stats["plans_created"]
            stats["purchases"] += demand_stats["purchases"]
            stats["rejections"] += demand_stats["rejections"]

        return stats

    def _process_preferred_pass(
        self, dealership: Dealership, run_id: uuid.UUID, now: Any
    ) -> dict[str, int]:
        """
        Pass 1: Purchasing models that match the dealership's preferences.

        For each preference, identify suitable CarModel instances and check the stock level
        in DealershipInventory. If stock is low or the model is missing, purchase more.
        """
        stats = {"plans_created": 0, "purchases": 0, "rejections": 0}

        preferences = DealershipPreference.objects.filter(
            dealer_id=dealership, is_active=True
        )

        for pref in preferences:
            car_models = CarModel.objects.filter(
                is_active=True,
                body_type=pref.body_type,
                fuel_type=pref.fuel_type,
                transmission=pref.transmission,
                drive_type=pref.drive_type,
                horsepower__gte=pref.min_hp,
                horsepower__lte=pref.max_hp,
            )

            for car_model in car_models:
                inventory = DealershipInventory.objects.filter(
                    dealer_id=dealership,
                    car_model=car_model,
                    is_active=True,
                ).first()

                current_qty = inventory.quantity if inventory else 0

                if current_qty < 5:
                    needed_qty = 5 - current_qty

                    result = self._create_purchase_plan_and_buy(
                        dealership=dealership,
                        car_model=car_model,
                        quantity=needed_qty,
                        pass_type=PurchasePlan.PassType.PREFERRED,
                        run_id=run_id,
                        now=now,
                        reason=f"preferred_pass_low_stock_{current_qty}",
                    )

                    stats["plans_created"] += 1
                    if result["purchased"]:
                        stats["purchases"] += 1
                    else:
                        stats["rejections"] += 1

        return stats

    def _process_demand_pass(
        self, dealership: Dealership, run_id: uuid.UUID, now: Any
    ) -> dict[str, int]:
        """
        Pass 2: Demand-based purchasing.

        Calculate average demand over 30 days (sales / 30).
        Calculate coverage in days (inventory balance / demand).
        Purchase if coverage ≤ 2 days.
        """
        stats = {"plans_created": 0, "purchases": 0, "rejections": 0}

        inventory_items = DealershipInventory.objects.filter(
            dealer_id=dealership, is_active=True, quantity__gte=0
        ).select_related("car_model")

        thirty_days_ago = now - timedelta(days=30)

        for inventory in inventory_items:
            car_model = inventory.car_model_id

            sales_qty = (
                SupplyHistory.objects.filter(
                    dealership=dealership,
                    car_model=car_model,
                    purchased_at__gte=thirty_days_ago,
                ).aggregate(total=Sum("quantity"))["total"]
                or 0
            )

            if sales_qty > 0:
                daily_demand = Decimal(sales_qty) / Decimal("30")
            else:
                daily_demand = Decimal("0")

            needed_qty, coverage_reason = self._calculate_needed_quantity(
                stock_qty=inventory.quantity,
                pending_incoming_qty=0,
                daily_demand=daily_demand,
            )

            if needed_qty > 0:
                result = self._create_purchase_plan_and_buy(
                    dealership=dealership,
                    car_model=car_model,
                    quantity=needed_qty,
                    pass_type=PurchasePlan.PassType.DEMAND,
                    run_id=run_id,
                    now=now,
                    reason=coverage_reason,
                )

                stats["plans_created"] += 1
                if result["purchased"]:
                    stats["purchases"] += 1
                else:
                    stats["rejections"] += 1
            else:
                PurchaseLog.objects.create(
                    run_id=run_id,
                    dealership=dealership,
                    car_model=car_model,
                    action="purchase_skipped",
                    reason=coverage_reason,
                    quantity=0,
                    unit_price=Decimal("0"),
                    payload={"daily_demand": str(daily_demand)},
                )
                stats["rejections"] += 1

        return stats

    def _calculate_needed_quantity(
        self,
        stock_qty: int,
        pending_incoming_qty: int,
        daily_demand: Decimal,
    ) -> tuple[int, str]:
        """
        Calculates the required quantity for purchase.

        Returns:
        tuple: (quantity, reason)
        """
        if daily_demand <= 0:
            return 0, "no_demand"

        available_qty = stock_qty + pending_incoming_qty
        coverage_days = Decimal(available_qty) / daily_demand

        if coverage_days >= NO_BUY_ABOVE_DAYS:
            return 0, f"coverage_{coverage_days:.2f}_above_threshold"

        if coverage_days > BUY_BELOW_DAYS:
            return 0, f"coverage_{coverage_days:.2f}_between_thresholds"

        target_qty = daily_demand * TARGET_COVERAGE_DAYS
        needed_qty = target_qty - Decimal(available_qty)

        if needed_qty <= 0:
            return 0, "no_needed_qty"

        return math.ceil(needed_qty), f"coverage_{coverage_days:.2f}_below_threshold"

    def _create_purchase_plan_and_buy(
        self,
        dealership: Dealership,
        car_model: CarModel,
        quantity: int,
        pass_type: str,
        run_id: uuid.UUID,
        now: Any,
        reason: str,
    ) -> dict[str, Any]:
        """
        Creates a PurchasePlan and executes the purchase via accept_supply_offer.

        Idempotency is ensured by a unique key based on the slot.
        """
        slot = floor_to_interval(now, SLOT_MINUTES)

        idempotency_key = (
            f"supply:{dealership.id}:{car_model.id}:{pass_type}:{slot.isoformat()}"
        )

        existing_plan = PurchasePlan.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        if existing_plan:
            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                action="purchase_skipped",
                reason="purchase_plan_already_exists",
                quantity=quantity,
                unit_price=Decimal("0"),
                payload={"plan_id": str(existing_plan.id)},
            )
            return {"purchased": False, "plan": existing_plan}

        best_supplier_link = DealershipSupplier.objects.filter(
            dealer_id=dealership,
            car_model=car_model,
            is_best=True,
            is_active=True,
        ).first()

        if not best_supplier_link:
            best_supplier_link = (
                DealershipSupplier.objects.filter(
                    dealer_id=dealership,
                    car_model=car_model,
                    is_active=True,
                )
                .order_by("best_price")
                .first()
            )

        if not best_supplier_link:
            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                action="purchase_skipped",
                reason="no_supplier_available",
                quantity=quantity,
                unit_price=Decimal("0"),
            )
            return {"purchased": False}

        supplier = best_supplier_link.supplier_id
        unit_price = best_supplier_link.best_price

        total_price = unit_price * Decimal(quantity)
        balance = dealership.account_id.get_balance()

        if balance < total_price:
            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                supplier=supplier,
                action="purchase_skipped",
                reason="insufficient_balance",
                quantity=quantity,
                unit_price=unit_price,
                payload={
                    "required": str(total_price),
                    "balance": str(balance),
                },
            )
            return {"purchased": False}

        plan = PurchasePlan.objects.create(
            dealership=dealership,
            car_model=car_model,
            supplier=supplier,
            pass_type=pass_type,
            slot=slot,
            status=PurchasePlan.Status.PENDING,
            quantity=quantity,
            unit_price=unit_price,
            idempotency_key=idempotency_key,
            reason=reason,
            payload={"slot": slot.isoformat()},
        )

        offer_expires_at = now + timedelta(hours=1)
        offer = Offer.objects.create(
            creator=dealership.account_id,
            car_model=car_model,
            quantity=quantity,
            max_price=unit_price,
            expires_at=offer_expires_at,
        )

        plan.offer = offer  # pyright: ignore[reportAttributeAccessIssue]
        plan.save(update_fields=["offer"])

        try:
            result = accept_supply_offer(offer=offer, supplier=supplier)

            plan.status = PurchasePlan.Status.COMPLETED
            plan.payload["supply_result"] = {
                "transaction_id": str(result.transaction.id),
                "total_price": str(result.total_price),
            }
            plan.save(update_fields=["status", "payload", "updated_at"])

            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                supplier=supplier,
                action="purchase_completed",
                reason=reason,
                quantity=quantity,
                unit_price=unit_price,
                payload={
                    "plan_id": str(plan.id),
                    "offer_id": str(offer.id),
                    "transaction_id": str(result.transaction.id),
                    "total_price": str(result.total_price),
                },
            )

            return {"purchased": True, "plan": plan, "result": result}

        except (
            OfferAlreadyProcessedError,
            OfferExpiredError,
            OfferRoleError,
            OutOfStockError,
        ) as exc:
            plan.status = PurchasePlan.Status.REJECTED
            plan.reason = str(exc)
            plan.save(update_fields=["status", "reason", "updated_at"])

            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                supplier=supplier,
                action="purchase_failed",
                reason=str(exc),
                quantity=quantity,
                unit_price=unit_price,
                payload={"plan_id": str(plan.id), "offer_id": str(offer.id)},
            )

            return {"purchased": False, "plan": plan}

        except Exception as exc:
            plan.status = PurchasePlan.Status.FAILED
            plan.reason = str(exc)
            plan.save(update_fields=["status", "reason", "updated_at"])

            PurchaseLog.objects.create(
                run_id=run_id,
                dealership=dealership,
                car_model=car_model,
                supplier=supplier,
                action="purchase_failed",
                reason=f"unexpected_error: {str(exc)}",
                quantity=quantity,
                unit_price=unit_price,
                payload={"plan_id": str(plan.id), "offer_id": str(offer.id)},
            )

            raise
