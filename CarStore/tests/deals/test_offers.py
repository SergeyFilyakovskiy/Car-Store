"""
Tests for Offer API endpoints.
"""

from datetime import timedelta
from typing import cast

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.response import Response
from tests.accounts.conftest import buyer_user
from tests.dealers.conftest import dealership_user
from tests.cars.conftest import car_model, car_brand


@pytest.mark.django_db
@pytest.mark.fast
class TestOfferListCreate:
    def test_create_offer_success(self, api_client, buyer_user, car_model):
        """Buyer can create an offer."""
        api_client.force_authenticate(user=buyer_user)
        payload = {
            "car_model": str(car_model.id),
            "max_price": "50000.00",
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        response = cast(
            Response,
            api_client.post(reverse("deals:offer-list-create"), payload, format="json"),
        )

        assert response.status_code == 201, response.data
        assert response.data["buyer"] == buyer_user.buyer.id  # pyright: ignore[reportOptionalSubscript]

    def test_create_offer_wrong_role(self, api_client, dealership_user, car_model):
        """Non-buyer cannot create an offer."""
        api_client.force_authenticate(user=dealership_user)
        payload = {
            "car_model": str(car_model.id),
            "max_price": "50000.00",
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        response = cast(
            Response,
            api_client.post(reverse("deals:offer-list-create"), payload, format="json"),
        )

        assert response.status_code in [401, 403]

    def test_list_offers_buyer(self, api_client, buyer_user, offer):
        """Buyer can list their own offers."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(Response, api_client.get(reverse("deals:offer-list-create")))

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestOfferDetail:
    def test_retrieve_offer_owner(self, api_client, buyer_user, offer):
        """Buyer can retrieve their own offer."""
        api_client.force_authenticate(user=buyer_user)
        response = cast(
            Response,
            api_client.get(reverse("deals:offer-detail", kwargs={"pk": offer.id})),
        )

        assert response.status_code == 200
        assert response.data["id"] == str(offer.id)  # pyright: ignore[reportOptionalSubscript]

    def test_update_offer_owner(self, api_client, buyer_user, offer):
        """Buyer can update their own offer."""
        api_client.force_authenticate(user=buyer_user)
        payload = {"max_price": "60000.00"}

        response = cast(
            Response,
            api_client.patch(
                reverse("deals:offer-detail", kwargs={"pk": offer.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        offer.refresh_from_db()
        assert offer.max_price == 60000.00
