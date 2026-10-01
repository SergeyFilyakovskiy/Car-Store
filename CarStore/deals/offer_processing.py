"""
Service to process incoming buyer offers.

Used in Problem 3.

Process:
1. Buyer verifications (balance > 0, email confirmed)
2. Search for salons with model and price <= max
3. Prioritization: min. price → active stock → history of successful sales
4. Transaction via accept_purchase_offer
5. Logging all steps
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from core.enums import StatusEnum
from dealers.models import Dealership, DealershipInventory, DealershipPromoModel
from django.db import transaction
from django.utils import timezone

from deals.exceptions import (
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OfferRoleError,
    OutOfStockError,
)
from deals.models import Offer, OfferLog, PurchaseHistory
from deals.services import accept_purchase_offer, calculate_purchase_unit_price


@dataclass
class DealershipCandidate:
    """Candidate salon to process the offer."""

    dealership: Dealership
    inventory: DealershipInventory
    unit_price: Decimal
    has_active_promo: bool
    success_sales_count: int


class OfferProcessingService:
    """Service to process an incoming buyer offer."""

    def process(self, offer_id: Any, run_id: uuid.UUID | None = None) -> dict[str, Any]:
        """
        Processes one offer.

        Args:
            offer_id: UUID of the offer
            run_id: UUID for the log group

        Returns:
            dict with the processing result
        """

        if run_id is None:
            run_id = uuid.uuid4()

        with transaction.atomic():
            offer = (
                Offer.objects.select_for_update()
                .select_related("creator", "car_model")
                .filter(id=offer_id)
                .first()
            )

            if offer is None:
                self._log(offer_id, run_id, "not_found", "skipped", "offer_not_found")
                return {"status": "not_found", "offer_id": str(offer_id)}

            if offer.status != StatusEnum.PENDING:
                self._log(
                    offer,
                    run_id,
                    "already_processed",
                    "skipped",
                    f"status_{offer.status}",
                )
                return {
                    "status": "already_processed",
                    "offer_id": str(offer.id),
                    "current_status": offer.status,
                }

            self._log(offer, run_id, "started", "processing", "")

            rejection_reason = self._validate_buyer(offer)
            if rejection_reason:
                self._reject_offer(offer, rejection_reason, run_id)
                return {
                    "status": "rejected",
                    "offer_id": str(offer.id),
                    "reason": rejection_reason,
                }

            candidates = self._find_candidates(offer)
            if not candidates:
                self._reject_offer(offer, "no_suitable_dealership", run_id)
                return {
                    "status": "rejected",
                    "offer_id": str(offer.id),
                    "reason": "no_suitable_dealership",
                }

            best = candidates[0]

            self._log(
                offer,
                run_id,
                "selected_dealership",
                "processing",
                "candidate_selected",
                payload={
                    "dealership_id": str(best.dealership.id),
                    "unit_price": str(best.unit_price),
                    "has_active_promo": best.has_active_promo,
                    "success_sales_count": best.success_sales_count,
                    "total_candidates": len(candidates),
                },
            )

            try:
                result = accept_purchase_offer(offer, best.dealership)

                self._log(
                    offer,
                    run_id,
                    "completed",
                    "completed",
                    "deal_accepted",
                    payload={
                        "dealership_id": str(best.dealership.id),
                        "transaction_id": str(result.transaction.id),
                        "total_price": str(result.total_price),
                        "unit_price": str(result.unit_price),
                        "quantity": result.quantity,
                    },
                )

                return {
                    "status": "completed",
                    "offer_id": str(offer.id),
                    "dealership_id": str(best.dealership.id),
                    "transaction_id": str(result.transaction.id),
                }

            except (
                OfferAlreadyProcessedError,
                OfferExpiredError,
                OfferRoleError,
                OutOfStockError,
            ) as exc:
                self._reject_offer(offer, str(exc), run_id)
                return {
                    "status": "rejected",
                    "offer_id": str(offer.id),
                    "reason": str(exc),
                }

            except Exception as exc:
                self._log(
                    offer,
                    run_id,
                    "failed",
                    "failed",
                    f"unexpected_error: {str(exc)}",
                )
                raise

    def _validate_buyer(self, offer: Offer) -> str | None:
        """
        Buyer checks before looking for salons.

        Returns:
            Reason for failure or None if everything is ok
        """
        buyer = offer.creator

        balance = buyer.get_balance()
        if balance <= Decimal("0"):
            return "buyer_balance_empty"

        if not buyer.is_verifyed:
            return "email_not_confirmed"

        return None

    def _find_candidates(self, offer: Offer) -> list[DealershipCandidate]:
        """
        Search for candidate salons for an offer.

        Criteria:
        - The salon is active
        - Model is available in quantity >= offer.quantity
        - Price sale_price <= offer.max_price

        Returns a sorted list of candidates."""
        today = timezone.now().date()

        inventory_items = DealershipInventory.objects.filter(
            is_active=True,
            car_model=offer.car_model,
            quantity__gte=offer.quantity,
        ).select_related("dealer_id")

        candidates = []

        for inventory in inventory_items:
            dealership = inventory.dealer_id

            if not dealership.is_active:
                continue

            unit_price = calculate_purchase_unit_price(offer, inventory)

            if unit_price > offer.max_price:
                continue

            has_active_promo = DealershipPromoModel.objects.filter(
                is_active=True,
                car_model=offer.car_model,
                promo__dealer=dealership,
                promo__is_active=True,
                promo__start_date__lte=today,
                promo__end_date__gte=today,
            ).exists()

            success_sales_count = PurchaseHistory.objects.filter(
                buyer=offer.creator.buyer,
                dealership=dealership,
            ).count()

            candidates.append(
                DealershipCandidate(
                    dealership=dealership,
                    inventory=inventory,
                    unit_price=unit_price,
                    has_active_promo=has_active_promo,
                    success_sales_count=success_sales_count,
                )
            )

        candidates.sort(
            key=lambda c: (
                c.unit_price,
                -int(c.has_active_promo),
                -c.success_sales_count,
            )
        )

        return candidates

    def _reject_offer(self, offer: Offer, reason: str, run_id: uuid.UUID) -> None:
        """Transfers the offer to CANCELLED status and logs the rejection."""
        offer.status = StatusEnum.CANCELLED
        offer.save(update_fields=["status", "updated_at"])

        self._log(offer, run_id, "rejected", "rejected", reason)

    def _log(self, offer, run_id, step, status, reason, payload=None):
        if not isinstance(offer, Offer):
            return
        try:
            OfferLog.objects.create(
                offer=offer,
                run_id=run_id,
                step=step,
                status=status,
                reason=reason,
                payload=payload or {},
            )
        except Exception:
            pass
