"""
Celery tasks for the dealers application
"""

import logging

from analytics.models import SalesStatistics
from celery import shared_task
from core.enums import StatusEnum
from deals.models import Offer, PurchaseHistory
from django.db.models import Count, Sum
from django.utils import timezone

from dealers.models import Dealership

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_sales_statistics(self, dealership_id=None):
    """
    Calculates and updates SalesStatistics for dealerships.

    Args:
        dealership_id: ID of a specific dealership (None = all)
    """

    try:
        if dealership_id:
            dealerships = Dealership.objects.filter(id=dealership_id)
        else:
            dealerships = Dealership.objects.all()

        for dealership in dealerships:
            stats = PurchaseHistory.objects.filter(dealership=dealership).aggregate(
                total_sales=Count("id"),
                total_revenue=Sum("price_paid"),
                total_cost=Count("cost_price"),
                unique_buyers=Count("buyer", distinct=True),
            )

            total_profit = (stats["total_revenue"] or 0) - (stats["total_cost"] or 0)

            SalesStatistics.objects.update_or_create(
                dealership=dealership,
                defaults={
                    "total_sales": stats["total_sales"] or 0,
                    "total_revenue": stats["total_revenue"] or 0,
                    "unique_buyers": stats["unique_buyers"] or 0,
                    "total_profit": total_profit or 0,
                    "calculated_at": timezone.now(),
                },
            )

            logger.info(f"Updated statistics for {dealership.name}")

        return f"Statistics calculated for {dealerships.count()} dealerships"
    except Exception as exc:
        logger.error(f"Error calculating statistics: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def expire_offer():
    """Marks expired offers as EXPIRED."""

    expired_count = Offer.objects.filter(
        status=StatusEnum.PENDING, expires_at__lt=timezone.now()
    ).update(status=StatusEnum.EXPIRED)

    logger.info(f"Expired {expired_count} offers")
    return f"Expired {expired_count} offers"
