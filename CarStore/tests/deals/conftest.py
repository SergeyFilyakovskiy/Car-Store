"""
Fixtures for the deals application tests.
Self-contained: does not import fixtures from other apps' conftest.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from tests.accounts.factories import (
    TransactionFactory,
    UserFactory,
    BuyerFactory,
)
from tests.cars.factories import CarBrandFactory, CarModelFactory
from tests.deals.factories import (
    OfferFactory,
    PurchaseHistoryFactory,
    SupplyHistoryFactory,
)
from tests.dealers.factories import DealershipFactory
from tests.suppliers.factories import SupplierFactory


# =============================================================================
# Users
# =============================================================================


@pytest.fixture
def buyer_user(db):
    """A user with the 'buyer' role and a Buyer profile."""
    buyer = BuyerFactory(
        user__username="deals_buyer",
        user__email="deals_buyer@example.com",
        user__role="buyer",
        user__balance=100000.00,
    )
    return buyer.user


@pytest.fixture
def dealership_user(db):
    """A user with the 'dealership' role."""
    return UserFactory(role="dealership", username="deals_dealer", email="deals_dealer@example.com")


@pytest.fixture
def supplier_user(db):
    """A user with the 'supplier' role."""
    return UserFactory(role="supplier", username="deals_supplier", email="deals_supplier@example.com")


@pytest.fixture
def other_dealership_user(db):
    """A different dealership user for isolation tests."""
    return UserFactory(role="dealership", username="deals_other_dealer", email="deals_other@example.com")


# =============================================================================
# Core entities
# =============================================================================


@pytest.fixture
def car_model(db):
    """A test car model."""
    brand = CarBrandFactory(name="Deals Brand", country="US")
    return CarModelFactory(brand=brand, name="Deals Model")


@pytest.fixture
def dealership(db, dealership_user):
    """A dealership owned by dealership_user."""
    return DealershipFactory(account_id=dealership_user, name="Deals Dealership")


@pytest.fixture
def other_dealership(db, other_dealership_user):
    """A dealership owned by other_dealership_user."""
    return DealershipFactory(account_id=other_dealership_user, name="Deals Other Dealership")


@pytest.fixture
def supplier(db, supplier_user):
    """A supplier owned by supplier_user."""
    return SupplierFactory(account_id=supplier_user, name="Deals Supplier")


# =============================================================================
# Deals entities
# =============================================================================


@pytest.fixture
def offer(db, buyer_user, car_model):
    """A pending offer created by buyer_user."""
    return OfferFactory(
        creator=buyer_user,
        car_model=car_model,
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def purchase_history(db, buyer_user, dealership, car_model, offer):
    """A purchase history record for buyer_user."""
    transaction = TransactionFactory(status="COMPLETED")
    return PurchaseHistoryFactory(
        buyer=buyer_user.buyer,
        dealership=dealership,
        car_model=car_model,
        offer=offer,
        transaction=transaction,
    )


@pytest.fixture
def supply_history(db, dealership, supplier, car_model):
    """A supply history record (dealership -> supplier)."""
    transaction = TransactionFactory(status="COMPLETED")
    offer = OfferFactory(
        creator=dealership.account_id,
        car_model=car_model,
        expires_at=timezone.now() + timedelta(days=30),
    )
    return SupplyHistoryFactory(
        dealership=dealership,
        supplier=supplier,
        car_model=car_model,
        offer=offer,
        transaction=transaction,
    )


# =============================================================================
# API clients
# =============================================================================


@pytest.fixture
def buyer_api_client(api_client, buyer_user):
    """An API client authenticated as buyer_user."""
    api_client.force_authenticate(user=buyer_user)
    return api_client


@pytest.fixture
def dealership_api_client(api_client, dealership_user):
    """An API client authenticated as dealership_user."""
    api_client.force_authenticate(user=dealership_user)
    return api_client


@pytest.fixture
def supplier_api_client(api_client, supplier_user):
    """An API client authenticated as supplier_user."""
    api_client.force_authenticate(user=supplier_user)
    return api_client
