"""
Tests for Offer API endpoints.
"""

from datetime import timedelta
from typing import Any

import pytest
from django.urls import reverse
from django.utils import timezone

LIST_CREATE_URL = "deals:offer-list-create"
DETAIL_URL = "deals:offer-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestOfferListCreate:
    """Tests for GET/POST /deals/offers/."""

    def test_create_offer_success(self, buyer_api_client, buyer_user, car_model):
        """A buyer can create an offer."""
        payload = {
            "car_model": str(car_model.id),
            "max_price": "50000.00",
            "quantity": 1,
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        response = buyer_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert str(_data(response)["creator"]) == str(buyer_user.id)
        assert _data(response)["status"] == "PENDING"

    def test_create_offer_wrong_role(self, dealership_api_client, car_model):
        """A non-buyer cannot create an offer."""
        payload = {
            "car_model": str(car_model.id),
            "max_price": "50000.00",
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 403

    def test_create_offer_unauthenticated(self, api_client, car_model):
        """An unauthenticated user cannot create an offer."""
        payload = {
            "car_model": str(car_model.id),
            "max_price": "50000.00",
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401

    def test_list_offers_buyer(self, buyer_api_client, offer):
        """A buyer can list their own offers."""
        response = buyer_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1

    def test_list_offers_isolated(
        self, buyer_api_client, offer, other_dealership_user, car_model
    ):
        """A buyer sees only their own offers, not others'."""
        OfferFactory = type(offer).__class__  # not used directly, but we need the factory
        from tests.deals.factories import OfferFactory

        OfferFactory(
            creator=other_dealership_user,
            car_model=car_model,
            expires_at=timezone.now() + timedelta(days=30),
        )

        response = buyer_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["creator"]) == str(offer.creator.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestOfferDetail:
    """Tests for GET/PATCH /deals/offers/<pk>/."""

    def test_retrieve_offer_owner(self, buyer_api_client, offer):
        """The owner can retrieve their offer."""
        response = buyer_api_client.get(reverse(DETAIL_URL, kwargs={"pk": offer.id}))

        assert response.status_code == 200
        assert _data(response)["id"] == str(offer.id)

    def test_update_offer_owner(self, buyer_api_client, offer):
        """The owner can update their offer."""
        payload = {"max_price": "60000.00"}

        response = buyer_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": offer.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200, _data(response)
        offer.refresh_from_db()
        assert offer.max_price == 60000.00

    def test_retrieve_offer_non_owner(
        self, buyer_api_client, other_dealership_user, car_model
    ):
        """A user cannot retrieve another user's offer."""
        from tests.deals.factories import OfferFactory

        other_offer = OfferFactory(
            creator=other_dealership_user,
            car_model=car_model,
            expires_at=timezone.now() + timedelta(days=30),
        )

        response = buyer_api_client.get(reverse(DETAIL_URL, kwargs={"pk": other_offer.id}))

        assert response.status_code == 404

    def test_retrieve_offer_unauthenticated(self, api_client, offer):
        """An unauthenticated user cannot retrieve an offer."""
        response = api_client.get(reverse(DETAIL_URL, kwargs={"pk": offer.id}))

        assert response.status_code == 401
