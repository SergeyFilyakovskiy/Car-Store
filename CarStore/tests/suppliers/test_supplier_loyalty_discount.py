"""
Tests for SupplierLoyaltyDiscount API endpoints.
"""

from typing import Any

import pytest
from django.urls import reverse
from suppliers.models import SupplierLoyaltyDiscount

LIST_CREATE_URL = "suppliers:loyalty-discount-list-create"
DETAIL_URL = "suppliers:loyalty-discount-detail"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierLoyaltyDiscountListCreate:
    """Tests for GET/POST /suppliers/loyalty-discounts/."""

    def test_create_loyalty_discount_success(
        self, supplier_api_client, supplier, dealership
    ):
        """The owner can create a loyalty discount for their supplier."""
        payload = {
            "supplier": str(supplier.id),
            "dealer": str(dealership.id),
            "discount_pct": "10.00",
            "min_purchases": 5,
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 201, _data(response)
        assert SupplierLoyaltyDiscount.objects.filter(
            supplier=supplier, dealer=dealership
        ).exists()

    def test_create_loyalty_discount_wrong_supplier(
        self, supplier_api_client, other_supplier, dealership
    ):
        """The owner cannot create a discount for another user's supplier."""
        payload = {
            "supplier": str(other_supplier.id),
            "dealer": str(dealership.id),
            "discount_pct": "10.00",
            "min_purchases": 5,
        }

        response = supplier_api_client.post(reverse(LIST_CREATE_URL), payload, format="json")

        assert response.status_code == 400
        assert "supplier" in _data(response)

    def test_list_loyalty_discounts_isolated(
        self, supplier_api_client, supplier_loyalty_discount, other_supplier, dealership
    ):
        """The owner sees only their own supplier's loyalty discounts."""
        SupplierLoyaltyDiscount.objects.create(
            supplier=other_supplier,
            dealer=dealership,
            discount_pct="5.00",
            min_purchases=3,
        )

        response = supplier_api_client.get(reverse(LIST_CREATE_URL))

        assert response.status_code == 200
        assert len(_data(response)) == 1
        assert str(_data(response)[0]["supplier"]) == str(supplier_loyalty_discount.supplier.id) # pyright: ignore[reportArgumentType]


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierLoyaltyDiscountDetail:
    """Tests for GET/PUT/PATCH/DELETE /suppliers/loyalty-discounts/<pk>/."""

    def test_update_loyalty_discount(self, supplier_api_client, supplier_loyalty_discount):
        """The owner can update a loyalty discount."""
        payload = {"discount_pct": "15.00"}

        response = supplier_api_client.patch(
            reverse(DETAIL_URL, kwargs={"pk": supplier_loyalty_discount.id}),
            payload,
            format="json",
        )

        assert response.status_code == 200
        supplier_loyalty_discount.refresh_from_db()
        assert supplier_loyalty_discount.discount_pct == 15.00

    def test_delete_loyalty_discount_non_owner(
        self, other_supplier_api_client, supplier_loyalty_discount
    ):
        """A non-owner cannot delete a loyalty discount."""
        response = other_supplier_api_client.delete(
            reverse(DETAIL_URL, kwargs={"pk": supplier_loyalty_discount.id})
        )

        assert response.status_code == 404
        assert SupplierLoyaltyDiscount.objects.filter(id=supplier_loyalty_discount.id).exists()
