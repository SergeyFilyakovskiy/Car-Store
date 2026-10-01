"""
Tests for Supplier API endpoints.
"""

from typing import Any

import pytest
from django.urls import reverse
from suppliers.models import Supplier

LIST_CREATE_URL = "suppliers:supplier-list-create"
DETAIL_URL = "suppliers:supplier-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierListCreate:
    """Tests for GET/POST /suppliers/."""

    def test_create_supplier_success(self, supplier_api_client, supplier_user):
        """A supplier user can create a supplier."""
        payload = {
            "name": "New Supplier",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test supplier",
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert Supplier.objects.filter(name="New Supplier").exists()
        assert str(_data(response)["account_id"]) == str(supplier_user.id)

    def test_create_supplier_wrong_role(self, buyer_api_client):
        """A user without 'supplier' role cannot create a supplier."""
        payload = {
            "name": "Hack Supplier",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test",
        }

        response = buyer_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 403

    def test_create_supplier_unauthenticated(self, api_client):
        """An unauthenticated user cannot create a supplier."""
        payload = {
            "name": "Unauth Supplier",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test",
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401

    def test_list_returns_all_suppliers(
        self, supplier_api_client, supplier, other_supplier
    ):
        """GET /suppliers/ returns all suppliers (not filtered by owner)."""
        response = supplier_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        # get_queryset returns Supplier.objects.all()
        assert len(_data(response)) == 2


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierDetail:
    """Tests for GET/PUT/PATCH/DELETE /suppliers/<pk>/."""

    def test_retrieve_supplier_owner(self, supplier_api_client, supplier):
        """The owner can retrieve their supplier."""
        response = supplier_api_client.get(reverse(DETAIL_URL, kwargs={"pk": supplier.id}))

        assert response.status_code == 200
        assert _data(response)["name"] == supplier.name

    def test_update_supplier_owner(self, supplier_api_client, supplier):
        """The owner can update their supplier."""
        payload = {"name": "Updated Supplier"}

        response = supplier_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": supplier.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        supplier.refresh_from_db()
        assert supplier.name == "Updated Supplier"

    def test_update_supplier_non_owner(self, other_supplier_api_client, supplier):
        """A non-owner cannot update the supplier."""
        payload = {"name": "Hacked Name"}

        response = other_supplier_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": supplier.id}),
            payload,
            format="json",
        )

        assert response.status_code == 403
        supplier.refresh_from_db()
        assert supplier.name != "Hacked Name"

    def test_delete_supplier_owner(self, supplier_api_client, supplier):
        """The owner can delete their supplier."""
        response = supplier_api_client.delete(reverse(DETAIL_URL, kwargs={"pk": supplier.id}))

        assert response.status_code == 204
        assert not Supplier.objects.filter(id=supplier.id).exists()

    def test_delete_supplier_non_owner(self, other_supplier_api_client, supplier):
        """A non-owner cannot delete the supplier."""
        response = other_supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier.id})
        )

        assert response.status_code == 403
        assert Supplier.objects.filter(id=supplier.id).exists()

    def test_retrieve_supplier_unauthenticated(self, api_client, supplier):
        """An unauthenticated user cannot retrieve supplier details."""
        response = api_client.get(reverse(DETAIL_URL, kwargs={"pk": supplier.id}))

        assert response.status_code == 401
