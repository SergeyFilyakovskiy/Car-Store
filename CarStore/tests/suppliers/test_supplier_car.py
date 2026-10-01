"""
Tests for SupplierCar API endpoints.
"""

from typing import Any

import pytest
from django.urls import reverse
from suppliers.models import SupplierCar

LIST_CREATE_URL = "suppliers:supplier-car-list-create"
DETAIL_URL = "suppliers:supplier-car-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierCarListCreate:
    """Tests for GET/POST /suppliers/cars/."""

    def test_create_supplier_car_success(
        self, supplier_api_client, supplier, car_model
    ):
        """The owner can add a car to their supplier's catalog."""
        payload = {
            "supplier": str(supplier.id),
            "car_model": str(car_model.id),
            "base_price": "35000.00",
            "stock_quantity": 10,
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert SupplierCar.objects.filter(supplier=supplier, car_model=car_model).exists()

    def test_create_supplier_car_wrong_supplier(
        self, supplier_api_client, other_supplier, car_model
    ):
        """The owner cannot add a car to another user's supplier."""
        payload = {
            "supplier": str(other_supplier.id),
            "car_model": str(car_model.id),
            "base_price": "35000.00",
            "stock_quantity": 10,
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "supplier" in _data(response)

    def test_list_supplier_cars_isolated(
        self, supplier_api_client, supplier_car, other_supplier, other_car_model
    ):
        """The owner sees only their own supplier's cars."""
        SupplierCar.objects.create(
            supplier=other_supplier,
            car_model=other_car_model,
            base_price="40000.00",
            stock_quantity=5,
        )

        response = supplier_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert _data(response)[0]["supplier"] == str(supplier_car.supplier.id) # pyright: ignore[reportArgumentType]

    def test_create_supplier_car_unauthenticated(self, api_client, supplier, car_model):
        """An unauthenticated user cannot create supplier cars."""
        payload = {
            "supplier": str(supplier.id),
            "car_model": str(car_model.id),
            "base_price": "35000.00",
            "stock_quantity": 10,
        }

        response = api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierCarDetail:
    """Tests for GET/PUT/PATCH/DELETE /suppliers/cars/<pk>/."""

    def test_update_supplier_car(self, supplier_api_client, supplier_car):
        """The owner can update a car offer."""
        payload = {"stock_quantity": 5}

        response = supplier_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": supplier_car.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        supplier_car.refresh_from_db()
        assert supplier_car.stock_quantity == 5

    def test_delete_supplier_car_non_owner(
        self, other_supplier_api_client, supplier_car
    ):
        """A non-owner cannot delete a car offer."""
        response = other_supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_car.id})
        )

        assert response.status_code == 404
        assert SupplierCar.objects.filter(id=supplier_car.id).exists()

    def test_delete_supplier_car_owner(self, supplier_api_client, supplier_car):
        """The owner can delete a car offer."""
        response = supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_car.id})
        )

        assert response.status_code == 204
        assert not SupplierCar.objects.filter(id=supplier_car.id).exists()
