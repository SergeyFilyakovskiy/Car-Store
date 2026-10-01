"""
Unit tests for custom permission classes in accounts.permissions.
Role permissions use Mock objects (no DB). Object-level permissions use the DB.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from accounts.models import Entry, Transaction
from accounts.permissions import (
    IsAdmin,
    IsBuyer,
    IsDealership,
    IsEmailVerified,
    IsOwnerProfile,
    IsSupplier,
    IsTransactionParticipant,
)


@pytest.mark.fast
class TestRolePermissions:
    """Tests for role-based permissions using mocks (no DB)."""

    def _make_request(self, is_authenticated: bool, role: str | None):
        """Helper to build a mock request."""
        request = Mock()
        request.user.is_authenticated = is_authenticated
        request.user.role = role
        return request

    def test_is_buyer(self):
        permission = IsBuyer()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert permission.has_permission(self._make_request(True, "buyer"), None) is True
        assert permission.has_permission(self._make_request(True, "supplier"), None) is False

    def test_is_supplier(self):
        permission = IsSupplier()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert permission.has_permission(self._make_request(True, "supplier"), None) is True
        assert permission.has_permission(self._make_request(True, "buyer"), None) is False

    def test_is_dealership(self):
        permission = IsDealership()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert permission.has_permission(self._make_request(True, "dealership"), None) is True

    def test_is_admin(self):
        permission = IsAdmin()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert permission.has_permission(self._make_request(True, "admin"), None) is True
        assert permission.has_permission(self._make_request(True, "buyer"), None) is False


@pytest.mark.fast
class TestIsEmailVerified:
    """Tests for the IsEmailVerified permission."""

    def _make_request(self, is_authenticated: bool, is_verifyed: bool | None):
        """Helper to build a mock request with the is_verifyed flag."""
        request = Mock()
        request.user.is_authenticated = is_authenticated
        request.user.is_verifyed = is_verifyed
        return request

    def test_verified_user_allowed(self):
        permission = IsEmailVerified()

        assert permission.has_permission(self._make_request(True, True), None) is True

    def test_unverified_user_denied(self):
        permission = IsEmailVerified()

        assert permission.has_permission(self._make_request(True, False), None) is False

    def test_unauthenticated_user_denied(self):
        permission = IsEmailVerified()

        assert permission.has_permission(self._make_request(False, True), None) is False


@pytest.mark.fast
class TestIsOwnerProfile:
    """Tests for the IsOwnerProfile object-level permission."""

    def test_unauthenticated_user(self):
        permission = IsOwnerProfile()
        request = Mock()
        request.user.is_authenticated = False

        assert permission.has_permission(request, None) is False

    def test_authenticated_user_no_object(self):
        permission = IsOwnerProfile()
        request = Mock()
        request.user.is_authenticated = True

        assert permission.has_permission(request, None) is True

    def test_owner_can_access_object(self, buyer_user, buyer_profile):
        permission = IsOwnerProfile()
        request = Mock()
        request.user = buyer_user

        assert permission.has_object_permission(request, None, buyer_profile) is True

    def test_non_owner_cannot_access_object(self, supplier_user, buyer_profile):
        permission = IsOwnerProfile()
        request = Mock()
        request.user = supplier_user

        assert permission.has_object_permission(request, None, buyer_profile) is False


@pytest.mark.django_db
@pytest.mark.fast
class TestIsTransactionParticipant:
    """Tests for the IsTransactionParticipant object-level permission.

    A user is a participant if they own at least one Entry in the transaction.
    """

    def _make_transaction_for(self, user):
        """Create a completed transaction with an entry owned by `user`."""
        txn = Transaction.objects.create(
            status=Transaction.Status.COMPLETED,
            idempotency_key=f"perm-tx-{user.id}",
            description="participant test",
        )
        Entry.objects.create(
            transaction=txn,
            user=user,
            amount=Decimal("10.00"),
            type=Entry.EntryType.CREDIT,
        )
        return txn

    def test_participant_allowed(self, buyer_user):
        permission = IsTransactionParticipant()
        txn = self._make_transaction_for(buyer_user)

        request = Mock()
        request.user = buyer_user

        assert permission.has_object_permission(request, None, txn) is True

    def test_non_participant_denied(self, buyer_user, user_factory):
        permission = IsTransactionParticipant()
        other_user = user_factory()
        txn = self._make_transaction_for(other_user)

        request = Mock()
        request.user = buyer_user

        assert permission.has_object_permission(request, None, txn) is False
