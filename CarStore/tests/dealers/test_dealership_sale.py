"""
Tests for DealershipSale API endpoints (Read-only).
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipSaleReadOnly:
    def test_list_sales_owner(
        self, api_client, dealership_user, dealership, dealership_sale
    ):
        """Owner can list sales for their dealership."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(Response, api_client.get(reverse("dealers:sale-list")))

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
        assert response.data[0]["dealership"] == str(dealership.id)  # pyright: ignore[reportOptionalSubscript]

    def test_list_sales_isolation(
        self, api_client, other_dealership_user, dealership_sale
    ):
        """Non-owner cannot see sales of another dealership."""
        api_client.force_authenticate(user=other_dealership_user)
        response = cast(Response, api_client.get(reverse("dealers:sale-list")))

        assert response.status_code == 200
        assert len(response.data) == 0  # pyright: ignore[reportArgumentType]

    def test_retrieve_sale_detail(self, api_client, dealership_user, dealership_sale):
        """Owner can retrieve details of a specific sale."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response,
            api_client.get(
                reverse("dealers:sale-detail", kwargs={"pk": dealership_sale.id})
            ),
        )

        assert response.status_code == 200
        assert response.data["sale_price"] == str(dealership_sale.sale_price)  # pyright: ignore[reportOptionalSubscript]

    def test_create_sale_blocked(self, api_client, dealership_user, dealership):
        """Direct POST to sales endpoint should be blocked (405 Method Not Allowed) as it's ListAPIView."""
        api_client.force_authenticate(user=dealership_user)
        payload = {"dealership": str(dealership.id)}  # Incomplete, but testing method

        response = cast(
            Response,
            api_client.post(reverse("dealers:sale-list"), payload, format="json"),
        )
        assert response.status_code == 405
