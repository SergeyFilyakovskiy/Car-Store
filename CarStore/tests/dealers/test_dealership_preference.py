"""
Tests for DealershipPreference API endpoints.
"""

from typing import cast

import pytest
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from dealers.models import DealershipPreference
from django.urls import reverse
from rest_framework.response import Response

from CarStore.tests.dealers.factories import DealershipPreferenceFactory


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipPreferenceCRUD:
    def test_create_preference_success(self, api_client, dealership_user, dealership):
        """Owner can create a preference for their dealership."""
        api_client.force_authenticate(user=dealership_user)
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

        response = cast(
            Response,
            api_client.post(
                reverse("dealers:preference-list-create"), payload, format="json"
            ),
        )
        assert response.status_code == 201, response.data
        assert DealershipPreference.objects.filter(dealer_id=dealership).exists()

    def test_create_preference_wrong_dealer(
        self, api_client, dealership_user, other_dealership
    ):
        """Owner cannot create a preference for another user's dealership."""
        api_client.force_authenticate(user=dealership_user)
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

        response = cast(
            Response,
            api_client.post(
                reverse("dealers:preference-list-create"), payload, format="json"
            ),
        )
        assert response.status_code == 400
        assert "dealer_id" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_list_preferences_isolated(
        self, api_client, dealership_user, dealership, other_dealership
    ):
        """User only sees their own dealership's preferences."""
        DealershipPreferenceFactory(dealer_id=dealership)
        DealershipPreferenceFactory(dealer_id=other_dealership)

        api_client.force_authenticate(user=dealership_user)
        response = cast(
            Response, api_client.get(reverse("dealers:preference-list-create"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
        assert response.data[0]["dealer_id"] == str(dealership.id)  # pyright: ignore[reportOptionalSubscript]

    def test_delete_preference_non_owner(
        self, api_client, other_dealership_user, dealership_preference
    ):
        """Non-owner cannot delete a preference."""
        api_client.force_authenticate(user=other_dealership_user)
        response = cast(
            Response,
            api_client.delete(
                reverse(
                    "dealers:preference-detail", kwargs={"pk": dealership_preference.id}
                )
            ),
        )

        assert response.status_code in [403, 404]
        assert DealershipPreference.objects.filter(id=dealership_preference.id).exists()
