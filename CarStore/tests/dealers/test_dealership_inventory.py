"""
Tests for DealershipInventory API endpoints.
"""

from typing import Any

import pytest
from dealers.models import DealershipInventory
from django.urls import reverse

LIST_CREATE_URL = "dealers:inventory-list-create"
DETAIL_URL = "dealers:inventory-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipInventoryListCreate:
    """Tests for GET/POST /dealers/inventory/."""

    def test_create_inventory_success(
        self, dealership_api_client, dealership, car_model
    ):
        """The owner can add a car model to their inventory."""
        payload = {
            "dealer_id": str(dealership.id),
            "car_model_id": str(car_model.id),
            "quantity": 5,
            "sale_price": "45000.00",
            "purchase_price": "30000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert DealershipInventory.objects.filter(
            dealer_id=dealership, car_model_id=car_model
        ).exists()

    def test_create_inventory_wrong_dealer(
        self, dealership_api_client, other_dealership, car_model
    ):
        """The owner cannot create inventory for another user's dealership."""
        payload = {
            "dealer_id": str(other_dealership.id),
            "car_model_id": str(car_model.id),
            "quantity": 5,
            "sale_price": "45000.00",
            "purchase_price": "30000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "dealer_id" in _data(response)

    def test_list_inventory_isolated(
        self, dealership_api_client, dealership_inventory, other_dealership, other_car_model
    ):
        """The owner sees only their own inventory."""
        DealershipInventory.objects.create(
            dealer_id=other_dealership,
            car_model_id=other_car_model,
            quantity=10,
            sale_price="50000.00",
            purchase_price="40000.00",
        )

        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["dealer_id"]) == str(dealership_inventory.dealer_id.id) # pyright: ignore[reportArgumentType]

    def test_create_inventory_unauthenticated(self, api_client, dealership, car_model):
        """An unauthenticated user cannot create inventory."""
        payload = {
            "dealer_id": str(dealership.id),
            "car_model_id": str(car_model.id),
            "quantity": 5,
            "sale_price": "45000.00",
            "purchase_price": "30000.00",
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipInventoryDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/inventory/<pk>/."""

    def test_update_quantity(self, dealership_api_client, dealership_inventory):
        """The owner can update the quantity of an existing inventory item."""
        payload = {"quantity": 2}

        response = dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership_inventory.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200, _data(response)
        dealership_inventory.refresh_from_db()
        assert dealership_inventory.quantity == 2

    def test_update_non_owner(self, other_dealership_api_client, dealership_inventory):
        """A non-owner cannot update inventory."""
        payload = {"quantity": 999}

        response = other_dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership_inventory.id}),
            payload,
            format="json",
        )

        assert response.status_code == 404
        dealership_inventory.refresh_from_db()
        assert dealership_inventory.quantity != 999

    def test_delete_inventory(self, dealership_api_client, dealership_inventory):
        """The owner can delete inventory."""
        response = dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_inventory.id})
        )

        assert response.status_code == 204
        assert not DealershipInventory.objects.filter(id=dealership_inventory.id).exists()
