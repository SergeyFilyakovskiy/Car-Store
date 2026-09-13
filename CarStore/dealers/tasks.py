"""
Celery tasks for the dealers application
"""

import logging
from decimal import Decimal

from analytics.models import SalesStatistics
from celery import shared_task
from core.enums import StatusEnum
from deals.models import Offer, PurchaseHistory
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from dealers.models import Dealership

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
