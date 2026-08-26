"""
Tests for Buyer Profile endpoints: Retrieve and Update.
"""

from typing import cast

import pytest
from core.enums import BodyTypesEnum, FuelTypeEnum
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestBuyerProfileRetrieve:
    """Tests for the BuyerProfileAPIView endpoint."""

    def test_get_profile_success(self, api_client, buyer_user):
        """Authenticated owner should successfully retrieve their profile."""
        api_client.force_authenticate(user=buyer_user)

        response = cast(Response, api_client.get(reverse("buyer-profile")))

        assert response.status_code == 200, response.data
        assert response.data["user"] == str(buyer_user.username)  # pyright: ignore[reportOptionalSubscript]
        assert response.data["country"] == buyer_user.buyer.country  # pyright: ignore[reportOptionalSubscript]

    def test_get_profile_unauthenticated(self, api_client):
        """Unauthenticated user should receive 401."""
        response = cast(Response, api_client.get(reverse("buyer-profile")))

        assert response.status_code == 401

    def test_get_profile_no_profile_exists(self, api_client, authenticated_user):
        """Authenticated user without a Buyer profile should receive 404."""

        api_client.force_authenticate(user=authenticated_user)

        response = cast(Response, api_client.get(reverse("buyer-profile")))

        # Note: Expects 404 if views use get_object_or_404.
        # If views use Buyer.objects.get(), it will return 500.
        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.fast
class TestBuyerProfileUpdate:
    """Tests for the BuyerProfileUpdateAPIView endpoint."""

    def test_update_profile_success(self, api_client, buyer_user):
        """Authenticated owner should successfully update their profile."""

        api_client.force_authenticate(user=buyer_user)

        payload = {
            "balance": 2500.50,
            "phone": "+9876543210",
            "country": "Canada",
            "preferred_body_type": BodyTypesEnum.CROSSOVER.value,
            "preferred_fuel_type": FuelTypeEnum.ELECTRIC.value,
        }

        response = cast(
            Response,
            api_client.patch(reverse("buyer-profile-update"), payload, format="json"),
        )

        assert response.status_code == 200, response.data
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.balance == 2500.50
        assert buyer_user.buyer.phone == "+9876543210"
        assert buyer_user.buyer.country == "Canada"

    def test_update_profile_unauthenticated(self, api_client, buyer_user):
        """Unauthenticated user should receive 401 when updating."""
        payload = {"balance": 9999.00}

        response = cast(
            Response,
            api_client.patch(reverse("buyer-profile-update"), payload, format="json"),
        )

        assert response.status_code == 401
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.balance != 9999.00

    def test_update_profile_wrong_user(self, api_client, supplier_user, buyer_user):
        """A different authenticated user should not be able to update the profile."""
        api_client.force_authenticate(user=supplier_user)
        payload = {"balance": 9999.00}

        response = cast(
            Response,
            api_client.patch(reverse("buyer-profile-update"), payload, format="json"),
        )

        # Should be 404 because IsOwnerProfile fails and get_object returns nothing/raises
        assert response.status_code in [403, 404]
        buyer_user.buyer.refresh_from_db()
        assert buyer_user.buyer.balance != 9999.00
