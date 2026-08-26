"""
Tests for Transaction API endpoints.
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from tests.accounts.conftest import buyer_user, supplier_user
from tests.dealers.conftest import dealership_user, other_dealership_user, dealership
from tests.suppliers.conftest import supplier
from tests.cars.conftest import car_brand, car_model


@pytest.mark.django_db
@pytest.mark.fast
class TestTransactionList:
    def test_list_transactions_buyer(self, api_client, buyer_user, transaction):
        """Buyer can list transactions they're involved in."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(Response, api_client.get(reverse("deals:transaction-list")))

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]

    def test_list_transactions_dealership(
        self, api_client, dealership_user, transaction
    ):
        """Dealership owner can list transactions they're involved in."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(Response, api_client.get(reverse("deals:transaction-list")))

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestTransactionDetail:
    def test_retrieve_transaction_participant(
        self, api_client, buyer_user, transaction
    ):
        """Transaction participant can retrieve transaction details."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(
            Response,
            api_client.get(
                reverse("deals:transaction-detail", kwargs={"pk": transaction.id})
            ),
        )

        assert response.status_code == 200
        assert response.data["amount"] == str(transaction.amount)  # pyright: ignore[reportOptionalSubscript]

    def test_retrieve_transaction_non_participant(
        self, api_client, other_dealership_user, transaction
    ):
        """Non-participant cannot retrieve transaction details."""
        api_client.force_authenticate(user=other_dealership_user)
        response = cast(
            Response,
            api_client.get(
                reverse("deals:transaction-detail", kwargs={"pk": transaction.id})
            ),
        )

        assert response.status_code in [403, 404]
