"""
Tests for the TopUp endpoints: create, status, cancel.
Requires the <uuid:id> route fix (Blocker 2).
"""

from decimal import Decimal
from typing import Any

import pytest
from django.urls import reverse

CREATE_TOPUP_URL = "create-topup"
TOPUP_STATUS_URL = "topup-status"
TOPUP_CANCEL_URL = "topup-cancel"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestCreateTopUp:
    """Tests for POST /topup/."""

    def test_create_topup_success(self, buyer_api_client):
        """An authenticated buyer can create a topup request."""
        payload = {"amount": "100.00", "payment_method": "CARD"}

        response = buyer_api_client.post(
            reverse(CREATE_TOPUP_URL), payload, format="json"
        )

        assert response.status_code == 201, _data(response)
        assert "topup_id" in _data(response)
        assert _data(response)["status"] == "PENDING"

    def test_create_topup_unauthenticated(self, api_client):
        """Unauthenticated users cannot create topups."""
        payload = {"amount": "100.00", "payment_method": "CARD"}

        response = api_client.post(reverse(CREATE_TOPUP_URL), payload, format="json")

        assert response.status_code == 401

    def test_create_topup_amount_too_large(self, buyer_api_client):
        """Amounts above the limit must be rejected."""
        payload = {"amount": "200000.00", "payment_method": "CARD"}

        response = buyer_api_client.post(
            reverse(CREATE_TOPUP_URL), payload, format="json"
        )

        assert response.status_code == 400

    def test_create_topup_negative_amount(self, buyer_api_client):
        """Negative or zero amounts must be rejected."""
        payload = {"amount": "0.00", "payment_method": "CARD"}

        response = buyer_api_client.post(
            reverse(CREATE_TOPUP_URL), payload, format="json"
        )

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.fast
class TestTopUpStatus:
    """Tests for GET /topup/<id>/."""

    def test_status_own_topup(self, buyer_api_client, buyer_user):
        """The owner can view their topup."""
        from accounts.models import BalanceTopUp

        topup = BalanceTopUp.objects.create(
            user=buyer_user,
            amount=Decimal("100.00"),
            payment_method="CARD",
            status="PENDING",
        )

        response = buyer_api_client.get(
            reverse(TOPUP_STATUS_URL, kwargs={"id": topup.id})
        )

        assert response.status_code == 200, _data(response)
        assert _data(response)["status"] == "PENDING"

    def test_status_foreign_topup_returns_404(self, buyer_api_client, user_factory):
        """A user cannot view someone else's topup."""
        from accounts.models import BalanceTopUp

        other_user = user_factory()
        topup = BalanceTopUp.objects.create(
            user=other_user,
            amount=Decimal("100.00"),
            payment_method="CARD",
            status="PENDING",
        )

        response = buyer_api_client.get(
            reverse(TOPUP_STATUS_URL, kwargs={"id": topup.id})
        )

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.fast
class TestTopUpCancel:
    """Tests for POST /topup/<id>/cancel/."""

    def test_cancel_own_pending_topup(self, buyer_api_client, buyer_user):
        """The owner can cancel their pending topup."""
        from accounts.models import BalanceTopUp

        topup = BalanceTopUp.objects.create(
            user=buyer_user,
            amount=Decimal("100.00"),
            payment_method="CARD",
            status="PENDING",
        )

        response = buyer_api_client.post(
            reverse(TOPUP_CANCEL_URL, kwargs={"id": topup.id})
        )

        assert response.status_code == 200
        topup.refresh_from_db()
        assert topup.status == "CANCELLED"

    def test_cancel_completed_topup_returns_409(self, buyer_api_client, buyer_user):
        """Cancelling a non-pending topup must return 409."""
        from accounts.models import BalanceTopUp

        topup = BalanceTopUp.objects.create(
            user=buyer_user,
            amount=Decimal("100.00"),
            payment_method="CARD",
            status="COMPLETED",
        )

        response = buyer_api_client.post(
            reverse(TOPUP_CANCEL_URL, kwargs={"id": topup.id})
        )

        assert response.status_code == 409
