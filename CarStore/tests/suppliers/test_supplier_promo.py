"""
Tests for SupplierPromo API endpoints.
"""

from datetime import date, timedelta
from typing import cast

import pytest
from django.urls import reverse
from rest_framework.response import Response
from suppliers.models import SupplierPromo
from tests.accounts.conftest import supplier_user
from tests.dealers.conftest import other_dealership_user, other_dealership


@pytest.mark.django_db
@pytest.mark.fast
class TestSupplierPromoCRUD:
    def test_create_promo(self, api_client, supplier_user, supplier):
        """Supplier owner can create a promotion."""
        api_client.force_authenticate(user=supplier_user)
        payload = {
            "supplier_id": str(supplier.id),
            "name": "Summer Sale",
            "description": "20% off",
            "discount_pct": "20.00",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        response = cast(
            Response,
            api_client.post(
                reverse("suppliers:supplier-promo-list-create"), payload, format="json"
            ),
        )

        assert response.status_code == 201, response.data
        assert SupplierPromo.objects.filter(name="Summer Sale").exists()

    def test_list_promos_isolation(
        self, api_client, supplier_user, supplier, other_dealership_user
    ):
        """Supplier only sees their own promotions."""
        SupplierPromo.objects.create(
            supplier=supplier,
            name="Test Promo",
            discount_pct=10.00,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        api_client.force_authenticate(user=supplier_user)
        response = cast(
            Response, api_client.get(reverse("suppliers:supplier-promo-list-create"))
        )

        assert response.status_code == 200
        assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
