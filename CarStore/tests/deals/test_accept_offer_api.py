"""
Tests for the Accept Offer API endpoints.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.urls import reverse
from django.utils import timezone
from dealers.models import DealershipInventory
from suppliers.models import SupplierCar

ACCEPT_PURCHASE_URL = "deals:offer-accept"
ACCEPT_SUPPLY_URL = "deals:offer-supply-accept"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.fixture
def buyer_offer(db, buyer_user, car_model):
    """A pending offer created by a buyer."""
    from tests.deals.factories import OfferFactory

    return OfferFactory(
        creator=buyer_user,
        car_model=car_model,
        quantity=1,
        max_price=Decimal("50000.00"),
        status="PENDING",
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def dealership_offer(db, dealership_user, car_model):
    """A pending offer created by a dealership."""
    from tests.deals.factories import OfferFactory

    return OfferFactory(
        creator=dealership_user,
        car_model=car_model,
        quantity=1,
        max_price=Decimal("40000.00"),
        status="PENDING",
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.mark.django_db
@pytest.mark.fast
class TestAcceptPurchaseOfferAPI:
    """Tests for POST /deals/offers/<offer_id>/accept/."""

    def test_accept_success(
        self, dealership_api_client, buyer_user, dealership, buyer_offer, car_model
    ):
        """A dealership owner can accept a buyer's offer."""
        DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=5,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("30000.00"),
        )
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        response = dealership_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 200, _data(response)
        assert _data(response)["offer_id"] == str(buyer_offer.id)
        assert "transaction_id" in _data(response)
        assert _data(response)["quantity"] == 1

        buyer_offer.refresh_from_db()
        assert buyer_offer.status == "COMPLETED"

    def test_accept_wrong_role(
        self, buyer_api_client, buyer_offer
    ):
        """A buyer cannot accept their own offer (needs dealership role)."""
        response = buyer_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 403

    def test_accept_unauthenticated(self, api_client, buyer_offer):
        """An unauthenticated user cannot accept an offer."""
        response = api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 401

    def test_accept_already_completed_returns_409(
        self, dealership_api_client, buyer_user, dealership, buyer_offer, car_model
    ):
        """Accepting an already-completed offer returns 409."""
        DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=5,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("30000.00"),
        )
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        # First acceptance
        dealership_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        # Second acceptance
        response = dealership_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 409

    def test_accept_insufficient_balance_returns_402(
        self, dealership_api_client, buyer_user, dealership, buyer_offer, car_model
    ):
        """A buyer without enough balance gets 402 Payment Required."""
        DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=5,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("30000.00"),
        )
        buyer_user.balance = Decimal("100.00")
        buyer_user.save(update_fields=["balance"])

        response = dealership_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 402

    def test_accept_out_of_stock_returns_409(
        self, dealership_api_client, buyer_user, dealership, buyer_offer, car_model
    ):
        """Accepting with no stock returns 409."""
        DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=0,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("30000.00"),
        )
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        response = dealership_api_client.post(
            reverse(ACCEPT_PURCHASE_URL, kwargs={"offer_id": buyer_offer.id})
        )

        assert response.status_code == 409


@pytest.mark.django_db
@pytest.mark.fast
class TestAcceptSupplyOfferAPI:
    """Tests for POST /deals/offers/<offer_id>/supply-accept/."""

    def test_accept_success(
        self, supplier_api_client, dealership_user, supplier, dealership_offer, car_model
    ):
        """A supplier owner can accept a dealership's offer."""
        SupplierCar.objects.create(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("35000.00"),
            stock_quantity=10,
        )
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        response = supplier_api_client.post(
            reverse(ACCEPT_SUPPLY_URL, kwargs={"offer_id": dealership_offer.id})
        )

        assert response.status_code == 200, _data(response)
        assert _data(response)["offer_id"] == str(dealership_offer.id)
        assert "transaction_id" in _data(response)

        dealership_offer.refresh_from_db()
        assert dealership_offer.status == "COMPLETED"

    def test_accept_wrong_role(self, dealership_api_client, dealership_offer):
        """A dealership cannot accept its own supply offer (needs supplier role)."""
        response = dealership_api_client.post(
            reverse(ACCEPT_SUPPLY_URL, kwargs={"offer_id": dealership_offer.id})
        )

        assert response.status_code == 403

    def test_accept_unauthenticated(self, api_client, dealership_offer):
        """An unauthenticated user cannot accept a supply offer."""
        response = api_client.post(
            reverse(ACCEPT_SUPPLY_URL, kwargs={"offer_id": dealership_offer.id})
        )

        assert response.status_code == 401

    def test_accept_out_of_stock_returns_409(
        self, supplier_api_client, dealership_user, supplier, dealership_offer, car_model
    ):
        """Accepting with no supplier stock returns 409."""
        SupplierCar.objects.create(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("35000.00"),
            stock_quantity=0,
        )
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        response = supplier_api_client.post(
            reverse(ACCEPT_SUPPLY_URL, kwargs={"offer_id": dealership_offer.id})
        )

        assert response.status_code == 409
