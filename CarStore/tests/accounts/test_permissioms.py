"""
Unit tests for custom permission classes in accounts.permissions.
Uses Mock objects to test logic without hitting the database.
"""

from unittest.mock import Mock

import pytest
from accounts.permissions import (
    IsAdmin,
    IsBuyer,
    IsDealership,
    IsOwnerProfile,
    IsSupplier,
)


@pytest.mark.fast
class TestRolePermissions:
    """Tests for role-based permissions: IsBuyer, IsSupplier, etc."""

    def _make_request(self, is_authenticated: bool, role: str | None):
        """Helper to create a mock request."""
        request = Mock()
        request.user.is_authenticated = is_authenticated
        request.user.role = role
        return request

    def test_is_buyer(self):
        permission = IsBuyer()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert (
            permission.has_permission(self._make_request(True, "buyer"), None) is True
        )
        assert (
            permission.has_permission(self._make_request(True, "supplier"), None)
            is False
        )

    def test_is_supplier(self):
        permission = IsSupplier()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert (
            permission.has_permission(self._make_request(True, "supplier"), None)
            is True
        )
        assert (
            permission.has_permission(self._make_request(True, "buyer"), None) is False
        )

    def test_is_dealership(self):
        permission = IsDealership()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert (
            permission.has_permission(self._make_request(True, "dealership"), None)
            is True
        )

    def test_is_admin(self):
        permission = IsAdmin()

        assert permission.has_permission(self._make_request(False, None), None) is False
        assert (
            permission.has_permission(self._make_request(True, "admin"), None) is True
        )
        assert (
            permission.has_permission(self._make_request(True, "buyer"), None) is False
        )


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

        # has_permission just checks auth
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
