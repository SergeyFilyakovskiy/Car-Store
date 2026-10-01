"""
Tests for DealershipPreference API endpoints.
"""

from typing import Any

import pytest
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from dealers.models import DealershipPreference
from django.urls import reverse
from tests.dealers.factories import DealershipPreferenceFactory

LIST_CREATE_URL = "dealers:preference-list-create"
DETAIL_URL = "dealers:preference-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPreferenceListCreate:
    """Tests for GET/POST /dealers/preferences/."""

    def test_create_preference_success(self, dealership_api_client, dealership):
        """The owner can create a preference for their dealership."""
        payload = {
            "dealer_id": str(dealership.id),
            "body_type": BodyTypesEnum.VAN.value,
            "fuel_type": FuelTypeEnum.DIESEL.value,
            "transmission": TransmissionTypeEnum.MT.value,
            "drive_type": DriveTypeEnum.AWD.value,
            "min_hp": 150,
            "max_hp": 300,
            "min_price": "20000.00",
            "max_price": "50000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert DealershipPreference.objects.filter(dealer_id=dealership).exists()

    def test_create_preference_wrong_dealer(
        self, dealership_api_client, other_dealership
    ):
        """The owner cannot create a preference for another user's dealership."""
        payload = {
            "dealer_id": str(other_dealership.id),
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "min_hp": 100,
            "max_hp": 200,
            "min_price": "10000.00",
            "max_price": "30000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "dealer_id" in _data(response)

    def test_list_preferences_isolated(
        self, dealership_api_client, dealership, other_dealership
    ):
        """The owner sees only their own dealership's preferences."""
        DealershipPreferenceFactory(dealer_id=dealership)
        DealershipPreferenceFactory(dealer_id=other_dealership)

        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["dealer_id"]) == str(dealership.id) # pyright: ignore[reportArgumentType]

    def test_create_preference_unauthenticated(self, api_client, dealership):
        """An unauthenticated user cannot create preferences."""
        payload = {
            "dealer_id": str(dealership.id),
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "min_hp": 100,
            "max_hp": 200,
            "min_price": "10000.00",
            "max_price": "30000.00",
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPreferenceDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/preferences/<pk>/."""

    def test_update_preference(self, dealership_api_client, dealership_preference):
        """The owner can update a preference."""
        payload = {"min_hp": 200}

        response = dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership_preference.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        dealership_preference.refresh_from_db()
        assert dealership_preference.min_hp == 200

    def test_delete_preference_non_owner(
        self, other_dealership_api_client, dealership_preference
    ):
        """A non-owner cannot delete a preference."""
        response = other_dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_preference.id})
        )

        assert response.status_code == 404
        assert DealershipPreference.objects.filter(id=dealership_preference.id).exists()

    def test_delete_preference_owner(self, dealership_api_client, dealership_preference):
        """The owner can delete a preference."""
        response = dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_preference.id})
        )

        assert response.status_code == 204
        assert not DealershipPreference.objects.filter(id=dealership_preference.id).exists()
