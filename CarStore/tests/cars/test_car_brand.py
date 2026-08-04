"""
Tests for CarBrand API endpoints.

Covers CRUD operations, permissions, and validation for car brand management.
"""

from typing import cast

import pytest
from cars.models import CarBrand
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestCarBrandListCreate:
    """Tests for CarBrand list and create endpoints."""

    def test_create_car_brand_authenticated(self, api_client_with_user):
        """Authenticated user can create a car brand."""
        payload = {
            "name": "BMW",
            "country": "Germany",
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-brand-list"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert CarBrand.objects.filter(name="BMW").exists()
        assert response.data["name"] == "BMW"  # pyright: ignore[reportOptionalSubscript]
        assert response.data["country"] == "Germany"  # pyright: ignore[reportOptionalSubscript]
        assert "id" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_create_car_brand_unauthenticated(self, api_client):
        """Unauthenticated user cannot create a car brand."""
        payload = {
            "name": "Unauth Brand",
            "country": "Unknown",
        }

        response = cast(
            Response, api_client.post(reverse("car-brand-list"), payload, format="json")
        )

        assert response.status_code in [401, 403]
        assert not CarBrand.objects.filter(name="Unauth Brand").exists()

    def test_create_car_brand_duplicate_name(self, api_client_with_user, car_brand):
        """Creating a brand with duplicate name should fail."""
        payload = {
            "name": car_brand.name,  # Duplicate
            "country": "Another Country",
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-brand-list"), payload, format="json"
            ),
        )

        assert response.status_code == 400
        assert "name" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_create_car_brand_missing_fields(self, api_client_with_user):
        """Creating a brand with missing required fields should fail."""
        payload = {
            "name": "Incomplete Brand",
            # Missing "country"
        }

        response = cast(
            Response,
            api_client_with_user.post(
                reverse("car-brand-list"), payload, format="json"
            ),
        )

        assert response.status_code == 400
        assert "country" in response.data  # pyright: ignore[reportOperatorIssue]

    def test_list_car_brands(self, api_client, multiple_car_brands):
        """Any user can list car brands."""
        response = cast(Response, api_client.get(reverse("car-brand-list")))

        assert response.status_code == 200
        assert len(response.data) == 5  # pyright: ignore[reportArgumentType]
        assert all("name" in brand for brand in response.data)  # pyright: ignore[reportOptionalIterable]
        assert all("country" in brand for brand in response.data)  # pyright: ignore[reportOptionalIterable]

    def test_list_car_brands_empty(self, api_client):
        """Listing brands when none exist returns empty list."""
        response = cast(Response, api_client.get(reverse("car-brand-list")))

        assert response.status_code == 200
        assert response.data == []


@pytest.mark.django_db
@pytest.mark.fast
class TestCarBrandDetail:
    """Tests for CarBrand detail endpoints."""

    def test_retrieve_car_brand(self, api_client, car_brand):
        """Any user can retrieve a car brand detail."""
        response = cast(
            Response,
            api_client.get(reverse("car-brand-detail", kwargs={"pk": car_brand.id})),
        )

        assert response.status_code == 200
        assert response.data["name"] == car_brand.name  # pyright: ignore[reportOptionalSubscript]
        assert response.data["country"] == car_brand.country  # pyright: ignore[reportOptionalSubscript]
        assert response.data["id"] == str(car_brand.id)  # pyright: ignore[reportOptionalSubscript]

    def test_retrieve_car_brand_not_found(self, api_client):
        """Retrieving non-existent brand returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = cast(
            Response,
            api_client.get(reverse("car-brand-detail", kwargs={"pk": fake_uuid})),
        )

        assert response.status_code == 404

    def test_update_car_brand_authenticated(self, api_client_with_user, car_brand):
        """Authenticated user can update a car brand."""
        payload = {
            "name": "Toyota Updated",
            "country": "Japan",
        }

        response = cast(
            Response,
            api_client_with_user.put(
                reverse("car-brand-detail", kwargs={"pk": car_brand.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        car_brand.refresh_from_db()
        assert car_brand.name == "Toyota Updated"

    def test_update_car_brand_unauthenticated(self, api_client, car_brand):
        """Unauthenticated user cannot update a car brand."""
        payload = {
            "name": "Hacked Brand",
            "country": "Unknown",
        }

        response = cast(
            Response,
            api_client.put(
                reverse("car-brand-detail", kwargs={"pk": car_brand.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code in [401, 403]
        car_brand.refresh_from_db()
        assert car_brand.name != "Hacked Brand"

    def test_partial_update_car_brand(self, api_client_with_user, car_brand):
        """Authenticated user can partially update a car brand."""
        payload = {
            "country": "Updated Country",
        }

        response = cast(
            Response,
            api_client_with_user.patch(
                reverse("car-brand-detail", kwargs={"pk": car_brand.id}),
                payload,
                format="json",
            ),
        )

        assert response.status_code == 200, response.data
        car_brand.refresh_from_db()
        assert car_brand.country == "Updated Country"
        assert car_brand.name != "Updated Country"  # Name unchanged

    def test_delete_car_brand_authenticated(self, api_client_with_user, car_brand):
        """Authenticated user can delete a car brand."""
        response = cast(
            Response,
            api_client_with_user.delete(
                reverse("car-brand-detail", kwargs={"pk": car_brand.id})
            ),
        )

        assert response.status_code == 204
        assert not CarBrand.objects.filter(id=car_brand.id).exists()

    def test_delete_car_brand_unauthenticated(self, api_client, car_brand):
        """Unauthenticated user cannot delete a car brand."""
        response = cast(
            Response,
            api_client.delete(reverse("car-brand-detail", kwargs={"pk": car_brand.id})),
        )

        assert response.status_code in [401, 403]
        assert CarBrand.objects.filter(id=car_brand.id).exists()
