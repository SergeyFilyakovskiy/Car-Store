"""
Tests for analytics API endpoints.
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from tests.dealers.conftest import (
    dealership_user,
    other_dealership_user,
    dealership,
    other_dealership,
)


@pytest.mark.django_db
@pytest.mark.fast
class TestSalesStatisticsList:
    def test_list_statistics_owner(self, api_client, dealership_user, sales_statistics):
        """Dealership owner can list their statistics."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response, api_client.get(reverse("analytics:sales-statistics-list"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
        assert response.data[0]["dealership"] == str(sales_statistics.dealership.id)  # pyright: ignore[reportOptionalSubscript]

    def test_list_statistics_wrong_role(self, api_client, authenticated_user):
        """Non-dealership user cannot access statistics."""
        api_client.force_authenticate(user=authenticated_user)  # role is 'buyer'
        response = cast(
            Response, api_client.get(reverse("analytics:sales-statistics-list"))
        )

        assert response.status_code in [401, 403]

    def test_list_statistics_isolation(
        self, api_client, dealership_user, sales_statistics, other_sales_statistics
    ):
        """Dealership owner only sees their own statistics."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response, api_client.get(reverse("analytics:sales-statistics-list"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestSalesStatisticsDetail:
    def test_retrieve_statistics_owner(
        self, api_client, dealership_user, sales_statistics
    ):
        """Dealership owner can retrieve their statistics."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response,
            api_client.get(
                reverse(
                    "analytics:sales-statistics-detail",
                    kwargs={"pk": sales_statistics.id},
                )
            ),
        )

        assert response.status_code == 200
        assert response.data["total_sales"] == sales_statistics.total_sales  # pyright: ignore[reportOptionalSubscript]
        assert response.data["total_revenue"] == str(sales_statistics.total_revenue)  # pyright: ignore[reportOptionalSubscript]

    def test_retrieve_statistics_non_owner(
        self, api_client, other_dealership_user, sales_statistics
    ):
        """Non-owner cannot retrieve another dealership's statistics."""
        api_client.force_authenticate(user=other_dealership_user)
        response = cast(
            Response,
            api_client.get(
                reverse(
                    "analytics:sales-statistics-detail",
                    kwargs={"pk": sales_statistics.id},
                )
            ),
        )

        assert response.status_code in [403, 404]
