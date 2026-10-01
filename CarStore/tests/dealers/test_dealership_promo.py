"""
Tests for DealershipPromo API endpoints.
"""

from datetime import date, timedelta
from typing import Any

import pytest
from dealers.models import DealershipPromo
from django.urls import reverse

LIST_CREATE_URL = "dealers:promo-list-create"
DETAIL_URL = "dealers:promo-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPromoListCreate:
    """Tests for GET/POST /dealers/promos/."""

    def test_create_promo_success(self, dealership_api_client, dealership):
        """The owner can create a promotion for their dealership."""
        today = date.today()
        payload = {
            "dealer": str(dealership.id),
            "name": "Summer Sale",
            "description": "10% off all cars",
            "discount_pct": "10.00",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert DealershipPromo.objects.filter(dealer=dealership, name="Summer Sale").exists()

    def test_create_promo_wrong_dealer(self, dealership_api_client, other_dealership):
        """The owner cannot create a promotion for another dealership."""
        today = date.today()
        payload = {
            "dealer": str(other_dealership.id),
            "name": "Hack Sale",
            "discount_pct": "99.00",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "dealer" in _data(response)

    def test_list_promos_isolated(
        self, dealership_api_client, dealership_promo, other_dealership
    ):
        """The owner sees only their own promotions."""
        DealershipPromo.objects.create(
            dealer=other_dealership,
            name="Other Promo",
            discount_pct="5.00",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert _data(response)[0]["dealer"] == str(dealership_promo.dealer.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPromoDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/promos/<pk>/."""

    def test_update_promo(self, dealership_api_client, dealership_promo):
        """The owner can update a promotion."""
        payload = {"name": "Updated Promo"}

        response = dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership_promo.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        dealership_promo.refresh_from_db()
        assert dealership_promo.name == "Updated Promo"

    def test_delete_promo_non_owner(self, other_dealership_api_client, dealership_promo):
        """A non-owner cannot delete a promotion."""
        response = other_dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_promo.id})
        )

        assert response.status_code == 404
        assert DealershipPromo.objects.filter(id=dealership_promo.id).exists()
