"""
Tests for DealershipPromoModel API endpoints.
"""

from typing import Any

import pytest
from dealers.models import DealershipPromoModel
from django.urls import reverse
from tests.cars.factories import CarBrandFactory, CarModelFactory

LIST_CREATE_URL = "dealers:promo-model-list-create"
DETAIL_URL = "dealers:promo-model-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPromoModelListCreate:
    """Tests for GET/POST /dealers/promo-models/."""

    def test_create_promo_model_success(
        self, dealership_api_client, dealership_promo, car_model
    ):
        """The owner can link a car model to their promotion."""
        payload = {
            "promo": str(dealership_promo.id),
            "car_model": str(car_model.id),
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert DealershipPromoModel.objects.filter(
            promo=dealership_promo, car_model=car_model
        ).exists()

    def test_create_promo_model_wrong_promo(
        self, dealership_api_client, dealership, other_dealership, car_model
    ):
        """The owner cannot link a car model to another dealership's promotion."""
        from tests.dealers.factories import DealershipPromoFactory

        other_promo = DealershipPromoFactory(dealer=other_dealership)
        payload = {
            "promo": str(other_promo.id),
            "car_model": str(car_model.id),
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "promo" in _data(response)

    def test_list_promo_models_isolated(
        self,
        dealership_api_client,
        dealership_promo_model,
        other_dealership,
        other_car_model,
    ):
        """The owner sees only their own promo-model links."""
        from tests.dealers.factories import DealershipPromoFactory

        other_promo = DealershipPromoFactory(dealer=other_dealership)
        DealershipPromoModel.objects.create(
            promo=other_promo, car_model=other_car_model
        )

        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["promo"]) == str(dealership_promo_model.promo.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPromoModelDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/promo-models/<pk>/."""

    def test_delete_promo_model_non_owner(
        self, other_dealership_api_client, dealership_promo_model
    ):
        """A non-owner cannot delete a promo-model link."""
        response = other_dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_promo_model.id})
        )

        assert response.status_code == 404
        assert DealershipPromoModel.objects.filter(id=dealership_promo_model.id).exists()

    def test_delete_promo_model_owner(
        self, dealership_api_client, dealership_promo_model
    ):
        """The owner can delete a promo-model link."""
        response = dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_promo_model.id})
        )

        assert response.status_code == 204
        assert not DealershipPromoModel.objects.filter(id=dealership_promo_model.id).exists()
