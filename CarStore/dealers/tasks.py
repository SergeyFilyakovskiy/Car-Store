"""
Celery tasks for the dealers application
"""

import logging
import uuid
from decimal import Decimal

from analytics.models import SalesStatistics
from celery import shared_task
from core.enums import StatusEnum
from deals.models import Offer, PurchaseHistory
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from dealers.models import Dealership
from dealers.services.purchase import PurchaseService
from dealers.services.supplier_actualization import SupplierActualizationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_sales_statistics(self, dealership_id):
    """
    Calculates and updates SalesStatistics for dealerships.

    Args:
        dealership_id: ID of a specific dealership
    """

    try:
        if dealership_id:
            dealership = Dealership.objects.get(id=dealership_id)

            stats = PurchaseHistory.objects.filter(dealership=dealership).aggregate(
                total_sales=Count("id"),
                total_revenue=Coalesce(Sum("price_paid"), Value(Decimal("0"))),
                total_cost=Coalesce(Sum("cost_price"), Value(Decimal("0"))),
                unique_buyers=Count("buyer", distinct=True),
            )

            total_profit = stats["total_revenue"] - stats["total_cost"]

            SalesStatistics.objects.update_or_create(
                dealership=dealership,
                defaults={
                    "total_sales": stats["total_sales"] or 0,
                    "total_revenue": stats["total_revenue"],
                    "unique_buyers": stats["unique_buyers"] or 0,
                    "total_profit": total_profit,
                    "calculated_at": timezone.now(),
                },
            )

            logger.info(f"Updated statistics for {dealership.name}")

            return {"new_statistics_for": dealership.name}

    except Dealership.DoesNotExist:
        logger.error(f"Dealership with id {dealership_id} does not exist")
        return {"status": "error", "reason": "dealership_not_found"}

    except Exception as exc:
        logger.error(f"Error calculating statistics: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def expire_offers():
    """Marks expired offers as EXPIRED."""

    expired_count = Offer.objects.filter(
        status=StatusEnum.PENDING, expires_at__lt=timezone.now()
    ).update(status=StatusEnum.EXPIRED)

    logger.info(f"Expired {expired_count} offers")
    return {"expired_count": expired_count}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def actualize_supplier_best_prices(self):
    """
    Updating best supplier prices (Task 2).

    Runs every hour. Recalculates `best_price` for all active
    `DealershipSupplier` records, taking into account promotions, loyalty programs, and potential discounts.
    """
    try:
        run_id = uuid.uuid4()
        service = SupplierActualizationService()
        stats = service.run(run_id=run_id)

        logger.info(
            f"Supplier prices actualized: {stats['updated_prices']} updated, "
            f"{stats['updated_is_best']} is_best flags changed, "
            f"{stats['logs_created']} logs created"
        )

        return {"run_id": str(run_id), "stats": stats}

    except Exception as exc:
        logger.error(f"Error actualizing supplier prices: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def purchase_from_suppliers(self):
    """
    Purchasing vehicles from suppliers (Task 1).

    Runs every 10 minutes. For each active dealership, it performs
    two passes: purchasing preferred cars and demand-based purchasing.
    """
    try:
        run_id = uuid.uuid4()
        service = PurchaseService()

        dealerships = Dealership.objects.filter(is_active=True)

        total_stats = {
            "run_id": str(run_id),
            "dealerships_processed": 0,
            "total_plans": 0,
            "total_purchases": 0,
            "total_rejections": 0,
        }

        for dealership in dealerships:
            stats = service.execute(dealership=dealership, run_id=run_id)

            total_stats["dealerships_processed"] += 1
            total_stats["total_plans"] += (
                stats["preferred_plans"] + stats["demand_plans"]
            )
            total_stats["total_purchases"] += stats["purchases"]
            total_stats["total_rejections"] += stats["rejections"]

        logger.info(
            f"Purchase task completed: {total_stats['dealerships_processed']} dealerships, "
            f"{total_stats['total_purchases']} purchases, "
            f"{total_stats['total_rejections']} rejections"
        )

        return total_stats

    except Exception as exc:
        logger.error(f"Error in purchase task: {exc}")
        raise self.retry(exc=exc)
