"""
Tests for DealershipSale API endpoints (Read-only).
"""

from typing import Any

import pytest
from django.urls import reverse

LIST_URL = "dealers:sale-list"
DETAIL_URL = "dealers:sale-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipSaleReadOnly:
    """Tests for GET /dealers/sales/."""

    def test_list_sales_owner(self, dealership_api_client, dealership, dealership_sale):
        """The owner can list sales for their dealership."""
        response = dealership_api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert _data(response)[0]["dealership"] == str(dealership.id) # pyright: ignore[reportArgumentType]

    def test_list_sales_isolation(
        self, other_dealership_api_client, dealership_sale
    ):
        """A non-owner cannot see sales of another dealership."""
        response = other_dealership_api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 0

    def test_retrieve_sale_detail(self, dealership_api_client, dealership_sale):
        """The owner can retrieve details of a specific sale."""
        response = dealership_api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": dealership_sale.id})
        )

        assert response.status_code == 200
        assert _data(response)["sale_price"] == str(dealership_sale.sale_price)

    def test_retrieve_sale_non_owner(self, other_dealership_api_client, dealership_sale):
        """A non-owner cannot retrieve sale details."""
        response = other_dealership_api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": dealership_sale.id})
        )

        assert response.status_code == 404

    def test_create_sale_blocked(self, dealership_api_client, dealership):
        """POST to sales endpoint should be blocked (405 Method Not Allowed)."""
        payload = {"dealership": str(dealership.id)}

        response = dealership_api_client.post(reverse(LIST_URL), payload, format="json")

        assert response.status_code == 405

    def test_list_sales_unauthenticated(self, api_client):
        """An unauthenticated user cannot list sales."""
        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 401
