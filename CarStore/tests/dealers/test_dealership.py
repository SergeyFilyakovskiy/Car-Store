"""
Tests for Dealership API endpoints.
"""

from typing import cast

import pytest
from dealers.models import Dealership
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipListCreate:
    def test_create_dealership_success(self, api_client, dealership_user):
        """Authenticated dealership user can create a dealership."""
        api_client.force_authenticate(user=dealership_user)
        payload = {
            "name": "New Auto Center",
            "country": "US",
            "address": "POINT(-73.935242 40.730610)",
            "balance": "50000.00",
        }

        response = cast(
            Response,
            api_client.post(
                reverse("dealers:dealership-list-create"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert Dealership.objects.filter(name="New Auto Center").exists()
        assert response.data["account_id"] == str(dealership_user.id)  # pyright: ignore[reportOptionalSubscript]

    def test_create_dealership_wrong_role(self, api_client, authenticated_user):
        """User without 'dealership' role cannot create a dealership."""
        api_client.force_authenticate(user=authenticated_user)  # role is 'buyer'
        payload = {
            "name": "Hack Center",
            "country": "US",
            "address": "POINT(0 0)",
            "balance": "100.00",
        }

        response = cast(
            Response,
            api_client.post(
                reverse("dealers:dealership-list-create"), payload, format="json"
            ),
        )
        assert response.status_code in [401, 403]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipDetail:
    def test_retrieve_dealership_owner(self, api_client, dealership_user, dealership):
        """Owner can retrieve their dealership details."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response,
            api_client.get(
                reverse("dealers:dealership-detail", kwargs={"pk": dealership.id})
            ),
        )

        assert response.status_code == 200
        assert response.data["name"] == dealership.name  # pyright: ignore[reportOptionalSubscript]

    def test_update_dealership_non_owner(
        self, api_client, other_dealership_user, dealership
    ):
        """Non-owner cannot update the dealership."""
        api_client.force_authenticate(user=other_dealership_user)
        payload = {
            "name": "Hacked Name",
            "country": "US",
            "address": "POINT(0 0)",
            "balance": "100.00",
        }

        response = cast(
            Response,
            api_client.put(
                reverse("dealers:dealership-detail", kwargs={"pk": dealership.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code in [403, 404]
        dealership.refresh_from_db()
        assert dealership.name != "Hacked Name"

    def test_delete_dealership_owner(self, api_client, dealership_user, dealership):
        """Owner can delete their dealership."""
        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response,
            api_client.delete(
                reverse("dealers:dealership-detail", kwargs={"pk": dealership.id})
            ),
        )

        assert response.status_code == 204
        assert not Dealership.objects.filter(id=dealership.id).exists()
