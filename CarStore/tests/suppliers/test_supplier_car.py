"""
Tests for SupplierCar API endpoints.
"""

from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from suppliers.models import SupplierCar
from tests.accounts.conftest import supplier_user
from tests.cars.conftest import car_model, car_brand


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierCarCRUD:
    def test_create_supplier_car(self, api_client, supplier_user, supplier, car_model):
        """Supplier owner can add a car to their catalog."""
        api_client.force_authenticate(user=supplier_user)
        payload = {
            "supplier_id": str(supplier.id),
            "car_model_id": str(car_model.id),
            "base_price": "35000.00",
            "stock_quantity": 10,
        }

        response = cast(
            Response,
            api_client.post(
                reverse("suppliers:supplier-car-list-create"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert SupplierCar.objects.filter(
            supplier_id=supplier, car_model_id=car_model
        ).exists()

    def test_list_supplier_cars(self, api_client, supplier_user, supplier, car_model):
        """Supplier owner can list their cars."""
        SupplierCar.objects.create(
            supplier_id=supplier,
            car_model_id=car_model,
            base_price=35000.00,
            stock_quantity=10,
        )

        api_client.force_authenticate(user=supplier_user)
        response = cast(
            Response, api_client.get(reverse("suppliers:supplier-car-list-create"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
