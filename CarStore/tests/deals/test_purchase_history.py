"""
Tests for PurchaseHistory API endpoints.
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from tests.accounts.conftest import buyer_user, supplier_user
from tests.dealers.conftest import dealership_user, dealership
from tests.cars.conftest import car_brand, car_model
from tests.suppliers.conftest import supplier


@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseHistoryList:
    def test_list_history_buyer(self, api_client, buyer_user, purchase_history):
        """Buyer can list their purchase history."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(
            Response, api_client.get(reverse("deals:purchase-history-list"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]

    def test_list_history_dealership(
        self, api_client, dealership_user, purchase_history
    ):
        """Dealership can list their sales history."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response, api_client.get(reverse("deals:purchase-history-list"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseHistoryDetail:
    def test_retrieve_history_buyer(self, api_client, buyer_user, purchase_history):
        """Buyer can retrieve their purchase details."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(
            Response,
            api_client.get(
                reverse(
                    "deals:purchase-history-detail", kwargs={"pk": purchase_history.id}
                )
            ),
        )

        assert response.status_code == 200
        assert response.data["price_paid"] == str(purchase_history.price_paid)  # pyright: ignore[reportOptionalSubscript]
