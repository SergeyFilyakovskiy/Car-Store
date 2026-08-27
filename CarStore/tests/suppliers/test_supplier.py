"""
Tests for Supplier API endpoints.
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from suppliers.models import Supplier
from tests.accounts.conftest import supplier_user
from tests.dealers.conftest import other_dealership_user


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierListCreate:
    def test_create_supplier_success(self, api_client, supplier_user):
        """Supplier user can create a supplier."""
        api_client.force_authenticate(user=supplier_user)
        payload = {
            "name": "New Supplier",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test supplier",
        }

        response = cast(
            Response,
            api_client.post(
                reverse("suppliers:supplier-list-create"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert Supplier.objects.filter(name="New Supplier").exists()

    def test_create_supplier_wrong_role(self, api_client, authenticated_user):
        """Non-supplier user cannot create a supplier."""
        api_client.force_authenticate(user=authenticated_user)  # role is 'buyer'
        payload = {
            "name": "Hack Supplier",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test",
        }

        response = cast(
            Response,
            api_client.post(
                reverse("suppliers:supplier-list-create"), payload, format="json"
            ),
        )

        assert response.status_code in [401, 403]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierDetail:
    def test_retrieve_supplier_owner(self, api_client, supplier_user, supplier):
        """Supplier owner can retrieve their supplier."""
        api_client.force_authenticate(user=supplier_user)
        response = cast(
            Response,
            api_client.get(
                reverse("suppliers:supplier-detail", kwargs={"pk": supplier.id})
            ),
        )

        assert response.status_code == 200
        assert response.data["name"] == supplier.name  # pyright: ignore[reportOptionalSubscript]

    def test_update_supplier_non_owner(
        self, api_client, other_dealership_user, supplier
    ):
        """Non-owner cannot update supplier."""
        api_client.force_authenticate(user=other_dealership_user)
        payload = {
            "name": "Hacked Name",
            "country": "US",
            "location": "POINT(0 0)",
            "founded_year": 2000,
            "description": "Test",
        }

        response = cast(
            Response,
            api_client.put(
                reverse("suppliers:supplier-detail", kwargs={"pk": supplier.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code in [403, 404]
