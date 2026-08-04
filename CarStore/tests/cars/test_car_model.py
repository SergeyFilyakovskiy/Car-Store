"""
Tests for CarModel API endpoints.

Covers CRUD operations, permissions, validation, and brand relationship handling.
"""

from typing import cast

import pytest
from cars.models import CarModel
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestCarModelListCreate:
    """Tests for CarModel list and create endpoints."""

    def test_create_car_model_authenticated(self, api_client_with_user, car_brand):
        """Authenticated user can create a car model."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Camry",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.5,
            "horsepower": 200,
            "year_form": 2020,
            "year_to": 2023,
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-model-list"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert CarModel.objects.filter(name="Camry").exists()
        assert response.data["name"] == "Camry"  # pyright: ignore[reportOptionalSubscript]
        assert response.data["brand"]["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]
        assert "brand_id" not in response.data  # pyright: ignore[reportOperatorIssue] # write_only field

    def test_create_car_model_unauthenticated(self, api_client, car_brand):
        """Unauthenticated user cannot create a car model."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Unauth Model",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.0,
            "horsepower": 150,
            "year_form": 2020,
            "year_to": 2023,
        }

        response = cast(
            Response, api_client.post(reverse("car-model-list"), payload, format="json")
        )

        assert response.status_code in [401, 403]
        assert not CarModel.objects.filter(name="Unauth Model").exists()

    def test_create_car_model_invalid_brand(self, api_client_with_user):
        """Creating a model with non-existent brand should fail."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        payload = {
            "brand_id": fake_uuid,
            "name": "Invalid Brand Model",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.0,
            "horsepower": 150,
            "year_form": 2020,
            "year_to": 2023,
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-model-list"), payload, format="json"
            ),
        )

        assert response.status_code == 400
        assert "brand_id" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_create_car_model_invalid_body_type(self, api_client_with_user, car_brand):
        """Creating a model with invalid body_type should fail."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Invalid Type Model",
            "body_type": "INVALID_TYPE",
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.0,
            "horsepower": 150,
            "year_form": 2020,
            "year_to": 2023,
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-model-list"), payload, format="json"
            ),
        )

        assert response.status_code == 400
        assert "body_type" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_create_car_model_missing_required_fields(
        self, api_client_with_user, car_brand
    ):
        """Creating a model with missing required fields should fail."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Incomplete Model",
            # Missing other required fields
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-model-list"), payload, format="json"
            ),
        )

        assert response.status_code == 400

    def test_create_car_model_optional_fields_null(
        self, api_client_with_user, car_brand
    ):
        """Creating a model with null optional fields should succeed."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Model With Nulls",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.0,
            "horsepower": None,  # Optional
            "year_form": None,  # Optional
            "year_to": None,  # Optional
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-model-list"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert response.data["horsepower"] is None  # pyright: ignore[reportOptionalSubscript]
        assert response.data["year_form"] is None  # pyright: ignore[reportOptionalSubscript]
        assert response.data["year_to"] is None  # pyright: ignore[reportOptionalSubscript]

    def test_list_car_models(self, api_client, multiple_car_models):
        """Any user can list car models."""
        response = cast(Response, api_client.get(reverse("car-model-list")))

        assert response.status_code == 200
        assert len(response.data) == 5  # pyright: ignore[reportArgumentType]
        assert all("name" in model for model in response.data)  # pyright: ignore[reportOptionalIterable]
        assert all("brand" in model for model in response.data)  # pyright: ignore[reportOptionalIterable]
        assert all(
            "brand" in model and "name" in model["brand"]
            for model in response.data  # pyright: ignore[reportOptionalIterable]
        )  # pyright: ignore[reportOptionalIterable]

    def test_list_car_models_empty(self, api_client):
        """Listing models when none exist returns empty list."""
        response = cast(Response, api_client.get(reverse("car-model-list")))

        assert response.status_code == 200
        assert response.data == []


@pytest.mark.django_db
@pytest.mark.fast
class TestCarModelDetail:
    """Tests for CarModel detail endpoints."""

    def test_retrieve_car_model(self, api_client, car_model):
        """Any user can retrieve a car model detail."""
        response = cast(
            Response,
            api_client.get(reverse("car-model-detail", kwargs={"pk": car_model.id})),
        )

        assert response.status_code == 200
        assert response.data["name"] == car_model.name  # pyright: ignore[reportOptionalSubscript]
        assert response.data["brand"]["name"] == car_model.brand.name  # pyright: ignore[reportOptionalSubscript]
        assert response.data["brand"]["country"] == car_model.brand.country  # pyright: ignore[reportOptionalSubscript]
        assert response.data["id"] == str(car_model.id)  # pyright: ignore[reportOptionalSubscript]

    def test_retrieve_car_model_not_found(self, api_client):
        """Retrieving non-existent model returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = cast(
            Response,
            api_client.get(reverse("car-model-detail", kwargs={"pk": fake_uuid})),
        )

        assert response.status_code == 404

    def test_update_car_model_authenticated(
        self, api_client_with_user, car_model, car_brand
    ):
        """Authenticated user can update a car model."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Camry Updated",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 3.0,
            "horsepower": 250,
            "year_form": 2021,
            "year_to": 2024,
        }

        response = cast(
            Response,
            api_client_with_user.put(
                reverse("car-model-detail", kwargs={"pk": car_model.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        car_model.refresh_from_db()
        assert car_model.name == "Camry Updated"
        assert car_model.engine_volume == 3.0

    def test_update_car_model_unauthenticated(self, api_client, car_model, car_brand):
        """Unauthenticated user cannot update a car model."""
        payload = {
            "brand_id": str(car_brand.id),
            "name": "Hacked Model",
            "body_type": BodyTypesEnum.SEDAN.value,
            "fuel_type": FuelTypeEnum.PETROL.value,
            "transmission": TransmissionTypeEnum.AT.value,
            "drive_type": DriveTypeEnum.FWD.value,
            "engine_volume": 2.0,
            "horsepower": 150,
            "year_form": 2020,
            "year_to": 2023,
        }

        response = cast(
            Response,
            api_client.put(
                reverse("car-model-detail", kwargs={"pk": car_model.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code in [401, 403]
        car_model.refresh_from_db()
        assert car_model.name != "Hacked Model"

    def test_partial_update_car_model(self, api_client_with_user, car_model):
        """Authenticated user can partially update a car model."""
        payload = {
            "horsepower": 300,
            "year_to": 2025,
        }

        response = cast(
            Response,
            api_client_with_user.patch(
                reverse("car-model-detail", kwargs={"pk": car_model.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        car_model.refresh_from_db()
        assert car_model.horsepower == 300
        assert car_model.year_to == 2025
        assert car_model.name != "300"  # Name unchanged

    def test_delete_car_model_authenticated(self, api_client_with_user, car_model):
        """Authenticated user can delete a car model."""
        response = cast(
            Response,
            api_client_with_user.delete(
                reverse("car-model-detail", kwargs={"pk": car_model.id})
            ),
        )

        assert response.status_code == 204
        assert not CarModel.objects.filter(id=car_model.id).exists()

    def test_delete_car_model_unauthenticated(self, api_client, car_model):
        """Unauthenticated user cannot delete a car model."""
        response = cast(
            Response,
            api_client.delete(reverse("car-model-detail", kwargs={"pk": car_model.id})),
        )

        assert response.status_code in [401, 403]
        assert CarModel.objects.filter(id=car_model.id).exists()

    def test_car_model_brand_relationship_integrity(
        self, api_client_with_user, car_brand, car_model
    ):
        """Deleting a brand should cascade delete related models."""
        # Create a model linked to the brand
        model_to_delete = CarModel.objects.create(
            brand=car_brand,
            name="Model To Delete",
            body_type=BodyTypesEnum.SEDAN.value,
            fuel_type=FuelTypeEnum.PETROL.value,
            transmission=TransmissionTypeEnum.AT.value,
            drive_type=DriveTypeEnum.FWD.value,
            engine_volume=2.0,
        )

        # Delete the brand
        car_brand.delete()

        # Model should be deleted due to CASCADE
        assert not CarModel.objects.filter(id=model_to_delete.id).exists()
