"""
Tests for DealershipInventory API endpoints.
"""

from typing import cast

import pytest
from dealers.models import DealershipInventory
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipInventoryCRUD:
    def test_create_inventory_success(
        self, api_client, dealership_user, dealership, car_model
    ):
        """Owner can add a car model to their inventory."""
        api_client.force_authenticate(user=dealership_user)
        payload = {
            "dealer_id": str(dealership.id),
            "car_model_id": str(car_model.id),
            "quantity": 5,
            "sale_price": "45000.00",
        }

        response = cast(
            Response,
            api_client.post(
                reverse("dealers:inventory-list-create"), payload, format="json"
            ),
        )
        assert response.status_code == 201, response.data
        assert DealershipInventory.objects.filter(
            dealer_id=dealership, car_model_id=car_model
        ).exists()

    def test_update_quantity(self, api_client, dealership_user, dealership_inventory):
        """Owner can update the quantity of an existing inventory item."""
        api_client.force_authenticate(user=dealership_user)
        payload = {"quantity": 2}

        response = cast(
            Response,
            api_client.patch(
                reverse(
                    "dealers:inventory-detail", kwargs={"pk": dealership_inventory.id}
                ),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        dealership_inventory.refresh_from_db()
        assert dealership_inventory.quantity == 2
