"""
Tests for Buyer Profile endpoints: retrieve and update.
"""

from typing import Any

import pytest
from core.enums import BodyTypesEnum, FuelTypeEnum
from django.urls import reverse

PROFILE_URL = "buyer-profile"
PROFILE_UPDATE_URL = "buyer-profile-update"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestBuyerProfileRetrieve:
    """Tests for the BuyerProfileAPIView endpoint."""

    def test_get_profile_success(self, buyer_api_client, buyer_user):
        """The owner can retrieve their profile."""
        response = buyer_api_client.get(reverse(PROFILE_URL))

        assert response.status_code == 200, _data(response)
        assert _data(response)["user"] == buyer_user.id
        assert _data(response)["country"] == buyer_user.buyer.country

    def test_get_profile_unauthenticated(self, api_client):
        """Unauthenticated users receive 401."""
        response = api_client.get(reverse(PROFILE_URL))

        assert response.status_code == 401

    def test_get_profile_no_profile_returns_404(self, supplier_api_client):
        """A user without a Buyer profile receives 404."""
        response = supplier_api_client.get(reverse(PROFILE_URL))

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.fast
class TestBuyerProfileUpdate:
    """Tests for the BuyerProfileUpdateAPIView endpoint."""

    def test_update_profile_success(self, buyer_api_client, buyer_user):
        """The owner can update their profile."""
        payload = {
            "balance": "2500.50",
            "phone": "+9876543210",
            "country": "Canada",
            "preferred_body_type": BodyTypesEnum.CROSSOVER.value,
            "preferred_fuel_type": FuelTypeEnum.ELECTRIC.value,
        }

        response = buyer_api_client.patch(
            reverse(PROFILE_UPDATE_URL), payload, format="json"
        )

        assert response.status_code == 200, _data(response)
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.phone == "+9876543210"
        assert buyer_user.buyer.country == "Canada"

    def test_update_profile_unauthenticated(self, api_client, buyer_user):
        """Unauthenticated users cannot update the profile."""
        payload = {"phone": "+1111111111"}

        response = api_client.patch(
            reverse(PROFILE_UPDATE_URL), payload, format="json"
        )

        assert response.status_code == 401
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.phone != "+1111111111"

    def test_update_profile_wrong_user(self, supplier_api_client, buyer_user):
        """A different user cannot update someone else's profile."""
        payload = {"phone": "+2222222222"}

        response = supplier_api_client.patch(
            reverse(PROFILE_UPDATE_URL), payload, format="json"
        )

        # 404 because supplier_user has no Buyer profile to match get_object_or_404
        assert response.status_code in (403, 404)
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.phone != "+2222222222"
