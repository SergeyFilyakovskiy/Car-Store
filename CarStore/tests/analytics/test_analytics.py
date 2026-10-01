"""
Tests for analytics API endpoints (sales statistics).
"""

from decimal import Decimal
from typing import Any

import pytest
from django.urls import reverse

LIST_URL = "analytics:sales-statistics-list"
DETAIL_URL = "analytics:sales-statistics-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSalesStatisticsList:
    """Tests for GET /analytics/ (list)."""

    def test_owner_sees_own_statistics(
        self, api_client, dealership_owner, sales_statistics
    ):
        """The owner sees their own statistics with the dealership name."""
        owner, dealership = dealership_owner
        api_client.force_authenticate(user=owner)

        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        results = _data(response)
        assert len(results) == 1
        assert results[0]["dealership"] == str(dealership.id) # pyright: ignore[reportArgumentType]
        assert results[0]["dealership_name"] == dealership.name # pyright: ignore[reportArgumentType]

    def test_unauthenticated_returns_401(self, api_client):
        """Unauthenticated users cannot list statistics."""
        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 401

    def test_wrong_role_returns_403(self, api_client, buyer_user):
        """A buyer (not a dealership) is rejected by IsDealership."""
        api_client.force_authenticate(user=buyer_user)

        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 403

    def test_isolation_between_dealerships(
        self, api_client, dealership_owner, sales_statistics, other_sales_statistics
    ):
        """An owner sees only their own statistics, not others'."""
        owner, _ = dealership_owner
        api_client.force_authenticate(user=owner)

        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_owner_without_statistics_gets_empty_list(self, api_client, dealership_owner):
        """An owner with no statistics record gets an empty list."""
        owner, _ = dealership_owner
        api_client.force_authenticate(user=owner)

        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 0


@pytest.mark.django_db
@pytest.mark.fast
class TestSalesStatisticsDetail:
    """Tests for GET /analytics/<pk>/ (detail)."""

    def test_owner_retrieves_own_statistics(
        self, api_client, dealership_owner, sales_statistics
    ):
        """The owner can retrieve their statistics with correct values."""
        owner, _ = dealership_owner
        api_client.force_authenticate(user=owner)

        response = api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": sales_statistics.id})
        )

        assert response.status_code == 200
        data = _data(response)
        assert data["total_sales"] == sales_statistics.total_sales
        assert Decimal(data["total_revenue"]) == sales_statistics.total_revenue
        assert data["unique_buyers"] == sales_statistics.unique_buyers
        assert Decimal(data["total_profit"]) == sales_statistics.total_profit

    def test_non_owner_cannot_retrieve(
        self, api_client, other_dealership_owner, sales_statistics
    ):
        """Another dealership owner cannot access foreign statistics."""
        other_owner, _ = other_dealership_owner
        api_client.force_authenticate(user=other_owner)

        response = api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": sales_statistics.id})
        )

        assert response.status_code == 404

    def test_unauthenticated_returns_401(self, api_client, sales_statistics):
        """Unauthenticated users cannot retrieve statistics."""
        response = api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": sales_statistics.id})
        )

        assert response.status_code == 401

    def test_buyer_cannot_retrieve(self, api_client, buyer_user, sales_statistics):
        """A buyer cannot retrieve dealership statistics."""
        api_client.force_authenticate(user=buyer_user)

        response = api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": sales_statistics.id})
        )

        # get_queryset filters by dealership__account_id, so the object is not found
        assert response.status_code == 404
