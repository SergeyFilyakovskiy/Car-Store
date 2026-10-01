"""
Celery tasks for the deals application.
"""

import logging
import uuid

from celery import shared_task
from core.enums import StatusEnum
from django.utils import timezone

from deals.models import Offer
from deals.offer_processing import OfferProcessingService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_offer(self, offer_id):
    """Processes a single incoming buyer offer (Task 3).

    It is triggered either by a signal following the creation of an offer
    or by the periodic task `process_pending_offers`.
    """
    try:
        run_id = uuid.uuid4()
        service = OfferProcessingService()
        result = service.process(offer_id=offer_id, run_id=run_id)

        logger.info(
            f"Offer {offer_id} processed: {result.get('status')} "
            f"(reason: {result.get('reason', 'none')})"
        )

        return result

    except Exception as exc:
        logger.error(f"Error processing offer {offer_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_pending_offers(self):
    """A periodic task for processing all pending offers.

    Runs every minute. Finds all offers with the status PENDING
    that have not yet expired and queues each one for processing.
    """
    try:
        now = timezone.now()

        offer_ids = list(
            Offer.objects.filter(
                status=StatusEnum.PENDING,
                expires_at__gt=now,
                is_active=True,
            )
            .order_by("created_at")
            .values_list("id", flat=True)[:200]
        )

        for offer_id in offer_ids:
            process_offer.delay(str(offer_id))  # pyright: ignore[reportCallIssue]

        logger.info(f"Scheduled {len(offer_ids)} pending offers for processing")

        return {"scheduled": len(offer_ids)}

    except Exception as exc:
        logger.error(f"Error scheduling pending offers: {exc}")
        raise self.retry(exc=exc)
