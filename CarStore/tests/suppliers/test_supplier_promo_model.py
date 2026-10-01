"""
Tests for SupplierPromoModel API endpoints.
"""

from typing import Any

import pytest
from django.urls import reverse
from suppliers.models import SupplierPromoModel

LIST_CREATE_URL = "suppliers:supplier-promo-model-list-create"
DETAIL_URL = "suppliers:supplier-promo-model-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierPromoModelListCreate:
    """Tests for GET/POST /suppliers/promo-models/."""

    def test_create_promo_model_success(
        self, supplier_api_client, supplier_promo, car_model
    ):
        """The owner can link a car model to their supplier's promotion."""
        payload = {
            "promo": str(supplier_promo.id),
            "car_model": str(car_model.id),
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert SupplierPromoModel.objects.filter(
            promo=supplier_promo, car_model=car_model
        ).exists()

    def test_create_promo_model_wrong_promo(
        self, supplier_api_client, other_supplier, car_model
    ):
        """The owner cannot link a car model to another supplier's promotion."""
        from tests.suppliers.factories import SupplierPromoFactory

        other_promo = SupplierPromoFactory(supplier=other_supplier)
        payload = {
            "promo": str(other_promo.id),
            "car_model": str(car_model.id),
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "promo" in _data(response)

    def test_list_promo_models_isolated(
        self,
        supplier_api_client,
        supplier_promo_model,
        other_supplier,
        other_car_model,
    ):
        """The owner sees only their own promo-model links."""
        from tests.suppliers.factories import SupplierPromoFactory

        other_promo = SupplierPromoFactory(supplier=other_supplier)
        SupplierPromoModel.objects.create(promo=other_promo, car_model=other_car_model)

        response = supplier_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert _data(response)[0]["promo"] == str(supplier_promo_model.promo.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierPromoModelDetail:
    """Tests for GET/PUT/PATCH/DELETE /suppliers/promo-models/<pk>/."""

    def test_delete_promo_model_non_owner(
        self, other_supplier_api_client, supplier_promo_model
    ):
        """A non-owner cannot delete a promo-model link."""
        response = other_supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_promo_model.id})
        )

        assert response.status_code == 404
        assert SupplierPromoModel.objects.filter(id=supplier_promo_model.id).exists()

    def test_delete_promo_model_owner(self, supplier_api_client, supplier_promo_model):
        """The owner can delete a promo-model link."""
        response = supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_promo_model.id})
        )

        assert response.status_code == 204
        assert not SupplierPromoModel.objects.filter(id=supplier_promo_model.id).exists()
