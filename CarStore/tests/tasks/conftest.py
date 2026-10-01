"""
Fixtures for Celery task tests.
Self-contained: uses factories directly, no cross-app fixture imports.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from tests.accounts.factories import BuyerFactory, TransactionFactory, UserFactory
from tests.cars.factories import CarBrandFactory, CarModelFactory
from tests.dealers.factories import (
    DealershipFactory,
    DealershipInventoryFactory,
    DealershipSupplierFactory,
)
from tests.deals.factories import OfferFactory, PurchaseHistoryFactory
from tests.suppliers.factories import (
    SupplierCarFactory,
    SupplierFactory,
    SupplierPromoFactory,
    SupplierPromoModelFactory,
)


# =============================================================================
# Factory fixtures (return the factory class for ad-hoc creation)
# =============================================================================


@pytest.fixture
def dealership_factory():
    """DealershipFactory for ad-hoc dealership creation."""
    return DealershipFactory


@pytest.fixture
def car_model_factory():
    """CarModelFactory for ad-hoc car model creation."""
    return CarModelFactory


@pytest.fixture
def supplier_factory():
    """SupplierFactory for ad-hoc supplier creation."""
    return SupplierFactory


@pytest.fixture
def inventory_factory():
    """DealershipInventoryFactory for ad-hoc inventory creation."""
    return DealershipInventoryFactory


@pytest.fixture
def dealership_supplier_factory():
    """DealershipSupplierFactory for ad-hoc supplier link creation."""
    return DealershipSupplierFactory


@pytest.fixture
def supplier_car_factory():
    """SupplierCarFactory for ad-hoc supplier car creation."""
    return SupplierCarFactory


@pytest.fixture
def supplier_promo_factory():
    """SupplierPromoFactory for ad-hoc supplier promo creation."""
    return SupplierPromoFactory


@pytest.fixture
def supplier_promo_model_factory():
    """SupplierPromoModelFactory for ad-hoc promo-model link creation."""
    return SupplierPromoModelFactory


# =============================================================================
# Users
# =============================================================================


@pytest.fixture
def buyer_user(db):
    """A user with the 'buyer' role and a Buyer profile."""
    buyer = BuyerFactory(
        user__username="tasks_buyer",
        user__email="tasks_buyer@example.com",
        user__role="buyer",
        user__balance=100000.00,
    )
    return buyer.user


@pytest.fixture
def dealership_user(db):
    """A user with the 'dealership' role."""
    return UserFactory(role="dealership", username="tasks_dealer", email="tasks_dealer@example.com")


@pytest.fixture
def other_dealership_user(db):
    """A different dealership user."""
    return UserFactory(role="dealership", username="tasks_other_dealer", email="tasks_other@example.com")


@pytest.fixture
def supplier_user(db):
    """A user with the 'supplier' role."""
    return UserFactory(role="supplier", username="tasks_supplier_user", email="tasks_supplier_user@example.com")


# =============================================================================
# Core entities
# =============================================================================


@pytest.fixture
def dealership(db, dealership_user):
    """A dealership owned by dealership_user."""
    return DealershipFactory(account_id=dealership_user, name="Tasks Dealership")


@pytest.fixture
def other_dealership(db, other_dealership_user):
    """A dealership owned by other_dealership_user."""
    return DealershipFactory(account_id=other_dealership_user, name="Tasks Other Dealership")


@pytest.fixture
def car_model(db):
    """A test car model."""
    brand = CarBrandFactory(name="Tasks Brand", country="US")
    return CarModelFactory(brand=brand, name="Tasks Model")


@pytest.fixture
def supplier(db, supplier_user):
    """A test supplier."""
    return SupplierFactory(account_id=supplier_user, name="Tasks Supplier")


@pytest.fixture
def inventory(db, dealership, car_model):
    """An inventory record for the test dealership."""
    return DealershipInventoryFactory(
        dealer_id=dealership,
        car_model_id=car_model,
        quantity=10,
        sale_price=Decimal("40000.00"),
        purchase_price=Decimal("30000.00"),
    )


@pytest.fixture
def offer(db, buyer_user, car_model):
    """A pending offer created by buyer_user."""
    return OfferFactory(
        creator=buyer_user,
        car_model=car_model,
        quantity=1,
        max_price=Decimal("50000.00"),
        status="PENDING",
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def purchase_history(db, buyer_user, dealership, car_model, offer):
    """A purchase history record for the test dealership."""
    transaction = TransactionFactory(status="COMPLETED")
    return PurchaseHistoryFactory(
        buyer=buyer_user.buyer,
        dealership=dealership,
        car_model=car_model,
        offer=offer,
        transaction=transaction,
        price_paid=Decimal("40000.00"),
        cost_price=Decimal("30000.00"),
    )
