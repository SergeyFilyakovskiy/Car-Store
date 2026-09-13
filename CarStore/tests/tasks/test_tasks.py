"""
Tests for Celery tasks.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from dealers.tasks import calculate_sales_statistics, expire_offers
from core.enums import StatusEnum
from tests.dealers.conftest import dealership, other_dealership, dealership_user, other_dealership_user
from tests.deals.conftest import purchase_history
from tests.deals.conftest import offer, transaction, purchase_history
from tests.accounts.conftest import buyer_user, supplier_user
from tests.cars.conftest import car_model, car_brand
from tests.suppliers.conftest import supplier

@pytest.mark.django_db
@pytest.mark.fast
class TestCalculateSalesStatistics:
    def test_calculate_statistics_success(self, dealership, purchase_history):
        """Task should calculate statistics for a dealership."""
        result = calculate_sales_statistics(dealership.id)

        assert result.get("new_statistics_for") == dealership.name

        from analytics.models import SalesStatistics
        stats = SalesStatistics.objects.get(dealership=dealership)
        assert stats.total_sales == 1
        assert stats.total_revenue == purchase_history.price_paid



@pytest.mark.django_db
@pytest.mark.fast
class TestExpireOffers:
    def test_expire_offers_success(self, offer):
        """Task should mark expired offers as EXPIRED."""

        offer.expires_at = timezone.now() - timedelta(days=1)
        offer.save()

        result = expire_offers()

        assert result.get("expired_count") == 1
        offer.refresh_from_db()
        assert offer.status == StatusEnum.EXPIRED

    def test_expire_offers_no_expired(self, offer):
        """Task should not affect non-expired offers."""
        result = expire_offers()

        assert result.get("expired_count") == 0
        offer.refresh_from_db()
        assert offer.status == StatusEnum.PENDING
