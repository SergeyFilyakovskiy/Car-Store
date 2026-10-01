"""
Tests for Transaction and Entry endpoints.
Participant model: a user participates in a transaction if they have
at least one Entry in it.
"""

from decimal import Decimal
from typing import Any

import pytest
from django.urls import reverse

TRANSACTION_LIST_URL = "transaction-list"
TRANSACTION_DETAIL_URL = "transaction-detail"
ENTRY_LIST_URL = "entry-list"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


def _make_transaction_with_entry(user, entry_type="CREDIT", amount="10.00"):
    """Create a completed transaction with a single entry owned by `user`."""
    from accounts.models import Entry, Transaction

    txn = Transaction.objects.create(
        status=Transaction.Status.COMPLETED,
        idempotency_key=f"tx-{user.id}-{entry_type}",
        description="test transaction",
    )
    Entry.objects.create(
        transaction=txn,
        user=user,
        amount=Decimal(amount),
        type=entry_type,
    )
    return txn


@pytest.mark.django_db
@pytest.mark.fast
class TestTransactionList:
    """Tests for GET /transactions/."""

    def test_list_returns_own_transactions(self, buyer_api_client, buyer_user):
        """A user sees transactions they participate in."""
        _make_transaction_with_entry(buyer_user)

        response = buyer_api_client.get(reverse(TRANSACTION_LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_list_excludes_foreign_transactions(
        self, buyer_api_client, buyer_user, user_factory
    ):
        """A user must not see transactions they are not part of."""
        other_user = user_factory()
        _make_transaction_with_entry(other_user)

        response = buyer_api_client.get(reverse(TRANSACTION_LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 0

    def test_list_unauthenticated(self, api_client):
        """Unauthenticated users cannot list transactions."""
        response = api_client.get(reverse(TRANSACTION_LIST_URL))

        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
class TestTransactionDetail:
    """Tests for GET /transactions/<pk>/."""

    def test_participant_can_view(self, buyer_api_client, buyer_user):
        """A participant can retrieve the transaction."""
        txn = _make_transaction_with_entry(buyer_user)

        response = buyer_api_client.get(
            reverse(TRANSACTION_DETAIL_URL, kwargs={"pk": txn.id})
        )

        assert response.status_code == 200, _data(response)
        assert _data(response)["id"] == str(txn.id)

    def test_non_participant_cannot_view(self, buyer_api_client, user_factory):
        """A non-participant receives 404."""
        other_user = user_factory()
        txn = _make_transaction_with_entry(other_user)

        response = buyer_api_client.get(
            reverse(TRANSACTION_DETAIL_URL, kwargs={"pk": txn.id})
        )

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.fast
class TestEntryList:
    """Tests for GET /entries/."""

    def test_list_returns_own_entries(self, buyer_api_client, buyer_user):
        """A user sees their own ledger entries."""
        _make_transaction_with_entry(buyer_user)

        response = buyer_api_client.get(reverse(ENTRY_LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_list_excludes_foreign_entries(
        self, buyer_api_client, user_factory
    ):
        """A user must not see other users' entries."""
        other_user = user_factory()
        _make_transaction_with_entry(other_user)

        response = buyer_api_client.get(reverse(ENTRY_LIST_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 0
