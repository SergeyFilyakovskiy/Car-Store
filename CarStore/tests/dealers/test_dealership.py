"""
Tests for Dealership API endpoints.
"""

from typing import Any

import pytest
from dealers.models import Dealership
from django.urls import reverse

LIST_CREATE_URL = "dealers:dealership-list-create"
DETAIL_URL = "dealers:dealership-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipListCreate:
    """Tests for GET/POST /dealers/."""

    def test_create_dealership_success(self, dealership_api_client, dealership_user):
        """An authenticated dealership user can create a dealership."""
        payload = {
            "name": "New Auto Center",
            "country": "US",
            "address": "POINT(-73.935242 40.730610)",
            "balance": "50000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert Dealership.objects.filter(name="New Auto Center").exists()
        assert str(_data(response)["account_id"]) == str(dealership_user.id)

    def test_create_dealership_wrong_role(self, buyer_api_client):
        """A user without 'dealership' role cannot create a dealership."""
        payload = {
            "name": "Hack Center",
            "country": "US",
            "address": "POINT(0 0)",
            "balance": "100.00",
        }

        response = buyer_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 403

    def test_create_dealership_unauthenticated(self, api_client):
        """An unauthenticated user cannot create a dealership."""
        payload = {
            "name": "Unauth Center",
            "country": "US",
            "address": "POINT(0 0)",
            "balance": "100.00",
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401

    def test_list_returns_all_dealerships(
        self, dealership_api_client, dealership, other_dealership
    ):
        """GET /dealers/ returns all dealerships (not filtered by owner)."""
        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        # get_queryset returns Dealership.objects.all()
        assert len(_data(response)) == 2


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/<pk>/."""

    def test_retrieve_dealership_owner(self, dealership_api_client, dealership):
        """The owner can retrieve their dealership details."""
        response = dealership_api_client.get(reverse(DETAIL_URL, kwargs={"pk": dealership.id}))

        assert response.status_code == 200
        assert _data(response)["name"] == dealership.name

    def test_update_dealership_owner(self, dealership_api_client, dealership):
        """The owner can update their dealership."""
        payload = {"name": "Updated Name"}

        response = dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        dealership.refresh_from_db()
        assert dealership.name == "Updated Name"

    def test_update_dealership_non_owner(self, other_dealership_api_client, dealership):
        """A non-owner cannot update the dealership."""
        payload = {"name": "Hacked Name"}

        response = other_dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership.id}),
            payload,
            format="json",
        )

        # IsDealershipOwner checks obj.account_id == request.user
        assert response.status_code == 403
        dealership.refresh_from_db()
        assert dealership.name != "Hacked Name"

    def test_delete_dealership_owner(self, dealership_api_client, dealership):
        """The owner can delete their dealership."""
        response = dealership_api_client.delete(reverse(DETAIL_URL, kwargs={"pk": dealership.id}))

        assert response.status_code == 204
        assert not Dealership.objects.filter(id=dealership.id).exists()

    def test_delete_dealership_non_owner(self, other_dealership_api_client, dealership):
        """A non-owner cannot delete the dealership."""
        response = other_dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership.id})
        )

        assert response.status_code == 403
        assert Dealership.objects.filter(id=dealership.id).exists()

    def test_retrieve_dealership_unauthenticated(self, api_client, dealership):
        """An unauthenticated user cannot retrieve dealership details."""
        response = api_client.get(reverse(DETAIL_URL, kwargs={"pk": dealership.id}))

        assert response.status_code == 401
