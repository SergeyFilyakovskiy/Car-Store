"""
A service for updating the best supplier prices.

Process:
1. For each active `DealershipSupplier`, recalculate `best_price` using `PricingService`.
2. If the price has changed, update and record the `SupplierPriceLog`.
3. For each (dealership, model) pair, identify the best supplier (lowest price).
4. Update the `is_best` flag.
"""

import uuid
from collections import defaultdict
from typing import Any

from django.utils import timezone

from dealers.models import (
    DealershipSupplier,
    SupplierPriceLog,
)
from dealers.services.pricing import get_supply_quote


class SupplierActualizationService:
    """A service for recalculating the best supplier prices."""

    def run(self, run_id: uuid.UUID | None = None) -> dict[str, Any]:
        """
        Initiates the full price update process.

        Returns:
            A dictionary containing statistics: the number of updated records, logs, etc.
        """
        if run_id is None:
            run_id = uuid.uuid4()

        stats = {
            "total_links": 0,
            "updated_prices": 0,
            "updated_is_best": 0,
            "logs_created": 0,
        }

        updated_count, logs = self._recalculate_best_prices(run_id)
        stats["updated_prices"] = updated_count
        stats["logs_created"] = len(logs)

        is_best_updated = self._update_is_best_flags()
        stats["updated_is_best"] = is_best_updated

        stats["total_links"] = DealershipSupplier.objects.filter(is_active=True).count()

        return stats

    def _recalculate_best_prices(
        self, run_id: uuid.UUID
    ) -> tuple[int, list[SupplierPriceLog]]:
        """
        Recalculates best_price for all active DealershipSupplier records.

        Returns:
            tuple: (number of updated records, list of created logs)
        """
        now = timezone.now()
        changed_objects = []
        logs = []

        queryset = (
            DealershipSupplier.objects.select_related(
                "dealership", "supplier", "car_model"
            )
            .filter(is_active=True)
            .order_by("dealership_id", "car_model_id", "id")
        )

        for link in queryset.iterator(chunk_size=500):
            quote = get_supply_quote(
                supplier=link.supplier_id,
                car_model=link.car_model_id,
                dealership=link.dealer_id,
                now=now,
            )

            new_price = quote.final_price
            old_price = link.best_price

            price_changed = old_price != new_price

            future_changed = (
                link.future_best_price != quote.future_best_price
                or link.future_best_price_date != quote.future_best_price_date
            )

            reason_changed = link.best_price_reason != quote.reason

            if price_changed or future_changed or reason_changed:
                link.best_price = new_price
                link.best_price_updated_at = now
                link.best_price_reason = quote.reason
                link.future_best_price = quote.future_best_price
                link.future_best_price_date = quote.future_best_price_date
                changed_objects.append(link)

                if price_changed:
                    logs.append(
                        SupplierPriceLog(
                            run_id=run_id,
                            dealership_supplier=link,
                            old_best_price=old_price,
                            new_best_price=new_price,
                            reason=quote.reason,
                            payload=self._build_payload(quote),
                        )
                    )

        if changed_objects:
            DealershipSupplier.objects.bulk_update(
                changed_objects,
                fields=[
                    "best_price",
                    "best_price_updated_at",
                    "best_price_reason",
                    "future_best_price",
                    "future_best_price_date",
                    "updated_at",
                ],
                batch_size=500,
            )

        if logs:
            SupplierPriceLog.objects.bulk_create(logs, batch_size=500)

        return len(changed_objects), logs

    def _update_is_best_flags(self) -> int:
        """
        Updates the `is_best` flag for each (salon, model) pair.

        The best supplier is the one with the lowest `best_price`.
        In the event of a price tie, the supplier with the lower ID is chosen.

        Returns:
            The number of updated records.
        """
        groups = defaultdict(list)

        queryset = DealershipSupplier.objects.filter(
            is_active=True, best_price__isnull=False
        ).order_by("dealership_id", "car_model_id", "best_price", "id")

        for link in queryset.iterator(chunk_size=500):
            key = (link.dealer_id_id, link.car_model_id_id)  # pyright: ignore[reportAttributeAccessIssue]
            groups[key].append(link)

        to_update = []

        for key, links in groups.items():
            sorted_links = sorted(links, key=lambda l: (l.best_price, l.supplier_id_id))  # noqa
            best = sorted_links[0]

            for link in links:
                new_is_best = link.id == best.id

                if link.is_best != new_is_best:
                    link.is_best = new_is_best
                    to_update.append(link)

        if to_update:
            DealershipSupplier.objects.bulk_update(
                to_update,
                fields=["is_best", "updated_at"],
                batch_size=500,
            )

        return len(to_update)

    def _build_payload(self, quote) -> dict[str, Any]:
        """Assembles the payload for SupplierPriceLog from SupplyQuote."""
        return {
            "base_price": str(quote.base_price),
            "promo_discount_pct": str(quote.promo_discount_pct),
            "loyalty_discount_pct": str(quote.loyalty_discount_pct),
            "total_discount_pct": str(quote.total_discount_pct),
            "stock_quantity": quote.stock_quantity,
            "promo_id": str(quote.promo_id) if quote.promo_id else None,
            "future_promo_discount_pct": (
                str(quote.future_promo_discount_pct)
                if quote.future_promo_discount_pct
                else None
            ),
        }
