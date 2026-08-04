from typing import cast

import pytest
from accounts.models import User
from cars.models import CarBrand, CarModel
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    user = User.objects.create_user(
        username="testuser",
        password="StrongPass123!",
        email="test@example.com",
        role="admin",
    )
    return user


@pytest.fixture
def car_brand(db):
    return CarBrand.objects.create(name="Toyota", country="Japan")


# ==================== CarBrand Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_brand(api_client, authenticated_user):
    """Brand creation must work for the authorized user."""
    api_client.force_authenticate(user=authenticated_user)

    payload = {
        "name": "BMW",
        "country": "Germany",
    }

    response = cast(
        Response, api_client.post(reverse("car-brand-list"), payload, format="json")
    )

    assert response.status_code == 201, response.data
    assert CarBrand.objects.filter(name="BMW").exists()
    assert response.data["name"] == "BMW"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["country"] == "Germany"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_get_car_brand_list(api_client, car_brand):
    """Retrieving the list of brands should work without authorization."""
    response = cast(Response, api_client.get(reverse("car-brand-list")))

    assert response.status_code == 200
    assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
    assert response.data[0]["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_get_car_brand_detail(api_client, car_brand):
    """Obtaining detailed information about the brand."""
    response = cast(
        Response,
        api_client.get(reverse("car-brand-detail", kwargs={"pk": car_brand.id})),
    )

    assert response.status_code == 200
    assert response.data["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["country"] == "Japan"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_update_car_brand(api_client, authenticated_user, car_brand):
    """The brand update must work for the authorized user."""
    api_client.force_authenticate(user=authenticated_user)

    payload = {
        "name": "Toyota Updated",
        "country": "Japan",
    }

    response = cast(
        Response,
        api_client.put(
            reverse("car-brand-detail", kwargs={"pk": car_brand.id}),
            payload,
            format="json",
        ),
    )

    assert response.status_code == 200, response.data
    car_brand.refresh_from_db()
    assert car_brand.name == "Toyota Updated"


@pytest.mark.django_db
@pytest.mark.fast
def test_delete_car_brand(api_client, authenticated_user, car_brand):
    """Brand deletion should work for an authorized user."""
    api_client.force_authenticate(user=authenticated_user)

    response = cast(
        Response,
        api_client.delete(reverse("car-brand-detail", kwargs={"pk": car_brand.id})),
    )

    assert response.status_code == 204
    assert not CarBrand.objects.filter(id=car_brand.id).exists()


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_brand_unauthenticated(api_client):
    """Creating a brand without authorization should return a 401 or 403 status code."""
    payload = {
        "name": "Unauth Brand",
        "country": "Unknown",
    }

    response = cast(
        Response, api_client.post(reverse("car-brand-list"), payload, format="json")
    )

    assert response.status_code in [401, 403]


# ==================== CarModel Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_model(api_client, authenticated_user, car_brand):
    """Creating a car model has to work."""
    api_client.force_authenticate(user=authenticated_user)

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
        Response, api_client.post(reverse("car-model-list"), payload, format="json")
    )

    assert response.status_code == 201, response.data
    assert CarModel.objects.filter(name="Camry").exists()
    assert response.data["brand"]["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["name"] == "Camry"  # pyright: ignore[reportOptionalSubscript]
    assert "brand_id" not in response.data  # pyright: ignore[reportOperatorIssue]


@pytest.mark.django_db
@pytest.mark.fast
def test_get_car_model_list(api_client, car_brand):
    """Retrieving the list of models should work without authorization."""
    CarModel.objects.create(
        brand=car_brand,
        name="Camry",
        body_type=BodyTypesEnum.SEDAN.value,
        fuel_type=FuelTypeEnum.PETROL.value,
        transmission=TransmissionTypeEnum.AT.value,
        drive_type=DriveTypeEnum.FWD.value,
        engine_volume=2.5,
        horsepower=200,
        year_form=2020,
        year_to=2023,
    )

    response = cast(Response, api_client.get(reverse("car-model-list")))

    assert response.status_code == 200
    assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
    assert response.data[0]["name"] == "Camry"  # pyright: ignore[reportOptionalSubscript]
    assert response.data[0]["brand"]["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_get_car_model_detail(api_client, car_brand):
    """Obtaining detailed information about the model."""
    car_model = CarModel.objects.create(
        brand=car_brand,
        name="Camry",
        body_type=BodyTypesEnum.SEDAN.value,
        fuel_type=FuelTypeEnum.PETROL.value,
        transmission=TransmissionTypeEnum.AT.value,
        drive_type=DriveTypeEnum.FWD.value,
        engine_volume=2.5,
        horsepower=200,
        year_form=2020,
        year_to=2023,
    )

    response = cast(
        Response,
        api_client.get(reverse("car-model-detail", kwargs={"pk": car_model.id})),
    )

    assert response.status_code == 200
    assert response.data["name"] == "Camry"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["brand"]["name"] == "Toyota"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_model_invalid_brand(api_client, authenticated_user):
    """Creating a model with a non-existent brand should return a 400 status code."""
    api_client.force_authenticate(user=authenticated_user)

    payload = {
        "brand_id": "00000000-0000-0000-0000-000000000000",  # Несуществующий UUID
        "name": "Invalid Model",
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
        Response, api_client.post(reverse("car-model-list"), payload, format="json")
    )

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_model_invalid_body_type(api_client, authenticated_user, car_brand):
    """Creating a model with an invalid body_type should return a 400."""
    api_client.force_authenticate(user=authenticated_user)

    payload = {
        "brand_id": str(car_brand.id),
        "name": "Invalid Model",
        "body_type": "INVALID_TYPE",  # Невалидное значение
        "fuel_type": FuelTypeEnum.PETROL.value,
        "transmission": TransmissionTypeEnum.AT.value,
        "drive_type": DriveTypeEnum.FWD.value,
        "engine_volume": 2.5,
        "horsepower": 200,
        "year_form": 2020,
        "year_to": 2023,
    }

    response = cast(
        Response, api_client.post(reverse("car-model-list"), payload, format="json")
    )

    assert response.status_code == 400
