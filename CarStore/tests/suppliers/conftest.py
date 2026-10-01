"""
Fixtures for the suppliers application tests.
Self-contained: does not import fixtures from other apps' conftest.
"""

import pytest
from tests.accounts.factories import UserFactory
from tests.cars.factories import CarBrandFactory, CarModelFactory
from tests.dealers.factories import DealershipFactory
from tests.suppliers.factories import (
    SupplierCarFactory,
    SupplierFactory,
    SupplierLoyaltyDiscountFactory,
    SupplierPromoFactory,
    SupplierPromoModelFactory,
)


# =============================================================================
# Users
# =============================================================================


@pytest.fixture
def supplier_user(db):
    """A user with the 'supplier' role."""
    return UserFactory(role="supplier", username="supplier_user", email="supplier@example.com")


@pytest.fixture
def other_supplier_user(db):
    """A different supplier user for isolation tests."""
    return UserFactory(role="supplier", username="other_supplier", email="other_supplier@example.com")


@pytest.fixture
def buyer_user(db):
    """A buyer user for wrong-role tests."""
    return UserFactory(role="buyer", username="supplier_buyer", email="supplier_buyer@example.com")


@pytest.fixture
def dealership_user(db):
    """A dealership user for loyalty discount tests."""
    return UserFactory(role="dealership", username="supplier_dealer", email="supplier_dealer@example.com")


# =============================================================================
# Core entities
# =============================================================================


@pytest.fixture
def supplier(db, supplier_user):
    """A supplier owned by supplier_user."""
    return SupplierFactory(account_id=supplier_user, name="Test Supplier")


@pytest.fixture
def other_supplier(db, other_supplier_user):
    """A supplier owned by other_supplier_user."""
    return SupplierFactory(account_id=other_supplier_user, name="Other Supplier")


@pytest.fixture
def car_model(db):
    """A test car model."""
    brand = CarBrandFactory(name="Supplier Brand", country="US")
    return CarModelFactory(brand=brand, name="Supplier Model")


@pytest.fixture
def other_car_model(db):
    """Another car model for uniqueness tests."""
    brand = CarBrandFactory(name="Supplier Other Brand", country="DE")
    return CarModelFactory(brand=brand, name="Supplier Other Model")


@pytest.fixture
def dealership(db, dealership_user):
    """A dealership for loyalty discount tests."""
    return DealershipFactory(account_id=dealership_user, name="Supplier Dealership")


# =============================================================================
# Supplier entities
# =============================================================================


@pytest.fixture
def supplier_car(db, supplier, car_model):
    """A car offer linked to the test supplier."""
    return SupplierCarFactory(supplier=supplier, car_model=car_model)


@pytest.fixture
def supplier_loyalty_discount(db, supplier, dealership):
    """A loyalty discount linked to the test supplier."""
    return SupplierLoyaltyDiscountFactory(supplier=supplier, dealer=dealership)


@pytest.fixture
def supplier_promo(db, supplier):
    """A promotion linked to the test supplier."""
    return SupplierPromoFactory(supplier=supplier)


@pytest.fixture
def supplier_promo_model(db, supplier_promo, car_model):
    """A promo-model link."""
    return SupplierPromoModelFactory(promo=supplier_promo, car_model=car_model)


# =============================================================================
# API clients
# =============================================================================


@pytest.fixture
def supplier_api_client(api_client, supplier_user):
    """An API client authenticated as supplier_user."""
    api_client.force_authenticate(user=supplier_user)
    return api_client


@pytest.fixture
def other_supplier_api_client(api_client, other_supplier_user):
    """An API client authenticated as other_supplier_user."""
    api_client.force_authenticate(user=other_supplier_user)
    return api_client


@pytest.fixture
def buyer_api_client(api_client, buyer_user):
    """An API client authenticated as buyer_user."""
    api_client.force_authenticate(user=buyer_user)
    return api_client
