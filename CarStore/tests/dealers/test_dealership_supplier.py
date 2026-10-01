"""
Tests for DealershipSupplier API endpoints.
"""

from typing import Any

import pytest
from dealers.models import DealershipSupplier
from django.urls import reverse
from tests.suppliers.factories import SupplierFactory

LIST_CREATE_URL = "dealers:supplier-list-create"
DETAIL_URL = "dealers:supplier-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipSupplierListCreate:
    """Tests for GET/POST /dealers/suppliers/."""

    def test_create_supplier_link_success(
        self, dealership_api_client, dealership, car_model
    ):
        """The owner can create a supplier link for their dealership."""
        supplier = SupplierFactory()
        payload = {
            "dealer_id": str(dealership.id),
            "supplier_id": str(supplier.id),
            "car_model_id": str(car_model.id),
            "best_price": "35000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert DealershipSupplier.objects.filter(
            dealer_id=dealership, supplier_id=supplier, car_model_id=car_model
        ).exists()

    def test_create_supplier_link_wrong_dealer(
        self, dealership_api_client, other_dealership, car_model
    ):
        """The owner cannot create a supplier link for another dealership."""
        supplier = SupplierFactory()
        payload = {
            "dealer_id": str(other_dealership.id),
            "supplier_id": str(supplier.id),
            "car_model_id": str(car_model.id),
            "best_price": "35000.00",
        }

        response = dealership_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "dealer_id" in _data(response)

    def test_list_supplier_links_isolated(
        self, dealership_api_client, dealership_supplier, other_dealership, other_car_model
    ):
        """The owner sees only their own supplier links."""
        supplier = SupplierFactory()
        DealershipSupplier.objects.create(
            dealer_id=other_dealership,
            supplier_id=supplier,
            car_model_id=other_car_model,
            best_price="40000.00",
        )

        response = dealership_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["dealer_id"]) == str(dealership_supplier.dealer_id.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestDealershipSupplierDetail:
    """Tests for GET/PUT/PATCH/DELETE /dealers/suppliers/<pk>/."""

    def test_update_supplier_link(self, dealership_api_client, dealership_supplier):
        """The owner can update a supplier link."""
        payload = {"best_price": "32000.00"}

        response = dealership_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": dealership_supplier.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        dealership_supplier.refresh_from_db()
        assert dealership_supplier.best_price == 32000.00

    def test_delete_supplier_link_non_owner(
        self, other_dealership_api_client, dealership_supplier
    ):
        """A non-owner cannot delete a supplier link."""
        response = other_dealership_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": dealership_supplier.id})
        )

        assert response.status_code == 404
        assert DealershipSupplier.objects.filter(id=dealership_supplier.id).exists()
