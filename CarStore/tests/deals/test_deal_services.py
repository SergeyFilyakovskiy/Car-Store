"""
Tests for the deal services: accept_purchase_offer and accept_supply_offer.
These are the core money-movement and stock-mutation tests.
"""

from decimal import Decimal

import pytest
from dealers.models import DealershipInventory
from deals.exceptions import (
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OfferRoleError,
    OutOfStockError,
)
from deals.models import PurchaseHistory, SupplyHistory
from deals.services import accept_purchase_offer, accept_supply_offer
from datetime import timedelta
from django.utils import timezone
from suppliers.models import SupplierCar
from tests.dealers.conftest import dealership

# =============================================================================
# Fixtures
# =============================================================================


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
    """A pending offer created by a dealership (for supply flow)."""
    from tests.deals.factories import OfferFactory

    return OfferFactory(
        creator=dealership_user,
        car_model=car_model,
        quantity=1,
        max_price=Decimal("40000.00"),
        status="PENDING",
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def stocked_inventory(db, dealership, car_model):
    """Dealership inventory with enough cars in stock."""
    return DealershipInventory.objects.create(
        dealer_id=dealership,
        car_model_id=car_model,
        quantity=5,
        sale_price=Decimal("40000.00"),
        purchase_price=Decimal("30000.00"),
    )


@pytest.fixture
def stocked_supplier_car(db, supplier, car_model):
    """Supplier stock with enough cars."""
    return SupplierCar.objects.create(
        supplier=supplier,
        car_model=car_model,
        base_price=Decimal("35000.00"),
        stock_quantity=10,
    )


# =============================================================================
# accept_purchase_offer (buyer -> dealership)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestAcceptPurchaseOffer:
    """Tests for the buyer -> dealership deal service."""

    def test_accept_success_completes_offer(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """A successful acceptance completes the offer and moves money."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        result = accept_purchase_offer(buyer_offer, dealership)

        assert result.offer.status == "COMPLETED"
        assert result.quantity == 1
        assert result.unit_price == Decimal("40000.00")
        assert result.total_price == Decimal("40000.00")

    def test_accept_success_decrements_inventory(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """Stock is decremented after a successful deal."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        accept_purchase_offer(buyer_offer, dealership)

        stocked_inventory.refresh_from_db()
        assert stocked_inventory.quantity == 4

    def test_accept_success_moves_money(
        self, buyer_user, dealership_user, dealership, buyer_offer, stocked_inventory
    ):
        """Money moves from buyer to dealership owner."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])
        initial_owner_balance = dealership_user.balance

        accept_purchase_offer(buyer_offer, dealership)

        buyer_user.refresh_from_db()
        dealership_user.refresh_from_db()
        assert buyer_user.balance == Decimal("60000.00")
        assert dealership_user.balance == initial_owner_balance + Decimal("40000.00")

    def test_accept_creates_purchase_history(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """A PurchaseHistory record is created."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        result = accept_purchase_offer(buyer_offer, dealership)

        history = PurchaseHistory.objects.filter(offer=buyer_offer).first()
        assert history is not None
        assert history.buyer == buyer_user.buyer
        assert history.dealership == dealership
        assert history.price_paid == result.total_price

    def test_accept_already_processed_raises(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """Accepting a non-PENDING offer raises OfferAlreadyProcessedError."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        accept_purchase_offer(buyer_offer, dealership)

        with pytest.raises(OfferAlreadyProcessedError):
            accept_purchase_offer(buyer_offer, dealership)

    def test_accept_idempotent_money(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """Replay after completion does not move money twice."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.save(update_fields=["balance"])

        accept_purchase_offer(buyer_offer, dealership)

        buyer_user.refresh_from_db()
        balance_after_first = buyer_user.balance

        with pytest.raises(OfferAlreadyProcessedError):
            accept_purchase_offer(buyer_offer, dealership)

        buyer_user.refresh_from_db()
        assert buyer_user.balance == balance_after_first

    def test_accept_expired_offer_raises(
        self, buyer_user, dealership, car_model, stocked_inventory
    ):
        """An expired offer raises OfferExpiredError."""
        from tests.deals.factories import OfferFactory

        expired_offer = OfferFactory(
            creator=buyer_user,
            car_model=car_model,
            quantity=1,
            max_price=Decimal("50000.00"),
            status="PENDING",
            expires_at=timezone.now() - timedelta(days=1),
        )

        with pytest.raises(OfferExpiredError):
            accept_purchase_offer(expired_offer, dealership)

    def test_accept_wrong_role_raises(
        self, dealership_user, dealership, dealership_offer, stocked_inventory
    ):
        """An offer created by a dealership cannot be accepted as a buyer deal."""
        with pytest.raises(OfferRoleError):
            accept_purchase_offer(dealership_offer, dealership)

    def test_accept_out_of_stock_raises(
        self, buyer_user, dealership, car_model, buyer_offer
    ):
        """Accepting with insufficient stock raises OutOfStockError."""
        DealershipInventory.objects.create(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=0,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("30000.00"),
        )

        with pytest.raises(OutOfStockError):
            accept_purchase_offer(buyer_offer, dealership)

    def test_accept_insufficient_balance_raises(
        self, buyer_user, dealership, buyer_offer, stocked_inventory
    ):
        """A buyer without enough balance triggers InsufficientBalanceError."""
        from accounts.exceptions import InsufficientBalanceError

        buyer_user.balance = Decimal("100.00")
        buyer_user.save(update_fields=["balance"])

        with pytest.raises(InsufficientBalanceError):
            accept_purchase_offer(buyer_offer, dealership)


# =============================================================================
# accept_supply_offer (dealership -> supplier)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestAcceptSupplyOffer:
    """Tests for the dealership -> supplier deal service."""

    def test_accept_success_completes_offer(
        self, dealership_user, supplier, dealership_offer, stocked_supplier_car, dealership
    ):
        """A successful supply acceptance completes the offer."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        result = accept_supply_offer(dealership_offer, supplier)

        assert result.offer.status == "COMPLETED"
        assert result.quantity == 1
        assert result.unit_price == Decimal("35000.00")
        assert result.total_price == Decimal("35000.00")

    def test_accept_success_decrements_supplier_stock(
        self, dealership_user, supplier, dealership_offer, stocked_supplier_car, dealership
    ):
        """Supplier stock is decremented after a successful deal."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        accept_supply_offer(dealership_offer, supplier)

        stocked_supplier_car.refresh_from_db()
        assert stocked_supplier_car.stock_quantity == 9

    def test_accept_success_creates_inventory(
        self, dealership_user, dealership, supplier, dealership_offer, stocked_supplier_car
    ):
        """First purchase of a model creates an inventory record."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        result = accept_supply_offer(dealership_offer, supplier)

        assert result.inventory is not None
        assert result.inventory.dealer_id == dealership
        assert result.inventory.quantity == 1

    def test_accept_success_moves_money(
        self, dealership_user, supplier_user, supplier, dealership_offer, stocked_supplier_car, dealership
    ):
        """Money moves from dealership owner to supplier owner."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])
        initial_supplier_balance = supplier_user.balance

        accept_supply_offer(dealership_offer, supplier)

        dealership_user.refresh_from_db()
        supplier_user.refresh_from_db()
        assert dealership_user.balance == Decimal("65000.00")
        assert supplier_user.balance == initial_supplier_balance + Decimal("35000.00")

    def test_accept_creates_supply_history(
        self, dealership_user, dealership, supplier, dealership_offer, stocked_supplier_car
    ):
        """A SupplyHistory record is created for loyalty tracking."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        result = accept_supply_offer(dealership_offer, supplier)

        history = SupplyHistory.objects.filter(offer=dealership_offer).first()
        assert history is not None
        assert history.dealership == dealership
        assert history.supplier == supplier
        assert history.total_price == result.total_price

    def test_accept_already_processed_raises(
        self, dealership_user, supplier, dealership_offer, stocked_supplier_car, dealership
    ):
        """Accepting a non-PENDING offer raises OfferAlreadyProcessedError."""
        dealership_user.balance = Decimal("100000.00")
        dealership_user.save(update_fields=["balance"])

        accept_supply_offer(dealership_offer, supplier)

        with pytest.raises(OfferAlreadyProcessedError):
            accept_supply_offer(dealership_offer, supplier)

    def test_accept_wrong_role_raises(
        self, buyer_user, supplier, buyer_offer, stocked_supplier_car, dealership
    ):
        """An offer created by a buyer cannot be accepted as a supply deal."""
        with pytest.raises(OfferRoleError):
            accept_supply_offer(buyer_offer, supplier)

    def test_accept_out_of_stock_raises(
        self, dealership_user, supplier, car_model, dealership_offer, dealership
    ):
        """Accepting with insufficient supplier stock raises OutOfStockError."""
        SupplierCar.objects.create(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("35000.00"),
            stock_quantity=0,
        )

        with pytest.raises(OutOfStockError):
            accept_supply_offer(dealership_offer, supplier)
