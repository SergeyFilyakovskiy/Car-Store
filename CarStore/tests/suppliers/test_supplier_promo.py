"""
Tests for SupplierPromo API endpoints.
"""

from datetime import date, timedelta
from typing import Any

import pytest
from django.urls import reverse
from suppliers.models import SupplierPromo

LIST_CREATE_URL = "suppliers:supplier-promo-list-create"
DETAIL_URL = "suppliers:supplier-promo-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierPromoListCreate:
    """Tests for GET/POST /suppliers/promos/."""

    def test_create_promo_success(self, supplier_api_client, supplier):
        """The owner can create a promotion for their supplier."""
        today = date.today()
        payload = {
            "supplier": str(supplier.id),
            "name": "Summer Sale",
            "description": "20% off",
            "discount_pct": "20.00",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert SupplierPromo.objects.filter(supplier=supplier, name="Summer Sale").exists()

    def test_create_promo_wrong_supplier(
        self, supplier_api_client, other_supplier
    ):
        """The owner cannot create a promotion for another user's supplier."""
        today = date.today()
        payload = {
            "supplier": str(other_supplier.id),
            "name": "Hack Sale",
            "discount_pct": "99.00",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "supplier" in _data(response)

    def test_list_promos_isolated(
        self, supplier_api_client, supplier_promo, other_supplier
    ):
        """The owner sees only their own supplier's promotions."""
        SupplierPromo.objects.create(
            supplier=other_supplier,
            name="Other Promo",
            discount_pct="5.00",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        response = supplier_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["supplier"]) == str(supplier_promo.supplier.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierPromoDetail:
    """Tests for GET/PUT/PATCH/DELETE /suppliers/promos/<pk>/."""

    def test_update_promo(self, supplier_api_client, supplier_promo):
        """The owner can update a promotion."""
        payload = {"name": "Updated Promo"}

        response = supplier_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": supplier_promo.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        supplier_promo.refresh_from_db()
        assert supplier_promo.name == "Updated Promo"

    def test_delete_promo_non_owner(self, other_supplier_api_client, supplier_promo):
        """A non-owner cannot delete a promotion."""
        response = other_supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_promo.id})
        )

        assert response.status_code == 404
        assert SupplierPromo.objects.filter(id=supplier_promo.id).exists()
