"""
Tests for PurchaseHistory API endpoints (Read-only).
"""

from typing import Any

import pytest
from django.urls import reverse

LIST_URL = "deals:purchase-history-list"
DETAIL_URL = "deals:purchase-history-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseHistoryList:
    """Tests for GET /deals/purchase-history/."""

    def test_list_history_buyer(self, buyer_api_client, purchase_history):
        """A buyer can list their purchase history."""
        response = buyer_api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_list_history_dealership(self, dealership_api_client, purchase_history):
        """A dealership owner can list their sales history."""
        response = dealership_api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_list_history_unauthenticated(self, api_client):
        """An unauthenticated user cannot list purchase history."""
        response = api_client.get(reverse(LIST_URL))

        assert response.status_code == 401

    def test_list_history_isolated(
        self, buyer_api_client, purchase_history, other_dealership_user, car_model, buyer_user
    ):
        """A buyer sees only their own purchase history."""
        from tests.deals.factories import PurchaseHistoryFactory
        from tests.accounts.factories import TransactionFactory
        from tests.dealers.factories import DealershipFactory

        other_dealership = DealershipFactory(account_id=other_dealership_user)
        other_transaction = TransactionFactory(status="COMPLETED")
        PurchaseHistoryFactory(
            buyer=buyer_user.buyer,  # same buyer, different dealership
            dealership=other_dealership,
            car_model=car_model,
            transaction=other_transaction,
        )

        response = buyer_api_client.get(reverse(LIST_URL))

        assert response.status_code == 200
        # Both records belong to the same buyer, so both are visible
        assert len(_data(response)) == 2


@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseHistoryDetail:
    """Tests for GET /deals/purchase-history/<pk>/."""

    def test_retrieve_history_buyer(self, buyer_api_client, purchase_history):
        """A buyer can retrieve their purchase details."""
        response = buyer_api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": purchase_history.id})
        )

        assert response.status_code == 200
        assert _data(response)["price_paid"] == str(purchase_history.price_paid)

    def test_retrieve_history_dealership(self, dealership_api_client, purchase_history):
        """A dealership owner can retrieve sale details."""
        response = dealership_api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": purchase_history.id})
        )

        assert response.status_code == 200

    def test_retrieve_history_non_participant(
        self, supplier_api_client, purchase_history
    ):
        """A non-participant cannot retrieve purchase details."""
        response = supplier_api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": purchase_history.id})
        )

        assert response.status_code == 404

    def test_retrieve_history_unauthenticated(self, api_client, purchase_history):
        """An unauthenticated user cannot retrieve purchase details."""
        response = api_client.get(
            reverse(DETAIL_URL, kwargs={"pk": purchase_history.id})
        )

        assert response.status_code == 401
