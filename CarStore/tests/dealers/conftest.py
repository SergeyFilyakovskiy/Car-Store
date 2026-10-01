"""
Fixtures for the dealers application tests.
"""

import pytest
from tests.accounts.factories import UserFactory
from tests.dealers.factories import (
    DealershipFactory,
    DealershipInventoryFactory,
    DealershipPreferenceFactory,
    DealershipPromoFactory,
    DealershipPromoModelFactory,
    DealershipSaleFactory,
    DealershipSupplierFactory,
)
from tests.cars.factories import CarBrandFactory, CarModelFactory


# =============================================================================
# Users
# =============================================================================


@pytest.fixture
def dealership_user(db):
    """A user with the 'dealership' role."""
    return UserFactory(role="dealership", username="dealer_user", email="dealer@example.com")


@pytest.fixture
def other_dealership_user(db):
    """A different dealership user for isolation tests."""
    return UserFactory(role="dealership", username="other_dealer", email="other@example.com")


@pytest.fixture
def buyer_user(db):
    """A buyer user for wrong-role tests."""
    return UserFactory(role="buyer", username="buyer_user", email="buyer@example.com")


# =============================================================================
# Dealerships
# =============================================================================


@pytest.fixture
def dealership(db, dealership_user):
    """A dealership owned by dealership_user."""
    return DealershipFactory(account_id=dealership_user, name="Test Dealership")


@pytest.fixture
def other_dealership(db, other_dealership_user):
    """A dealership owned by other_dealership_user."""
    return DealershipFactory(account_id=other_dealership_user, name="Other Dealership")


# =============================================================================
# Car models
# =============================================================================


@pytest.fixture
def car_model(db):
    """A test car model."""
    brand = CarBrandFactory(name="Test Brand", country="US")
    return CarModelFactory(brand=brand, name="Test Model")


@pytest.fixture
def other_car_model(db):
    """Another car model for uniqueness tests."""
    brand = CarBrandFactory(name="Other Brand", country="DE")
    return CarModelFactory(brand=brand, name="Other Model")


# =============================================================================
# Dealership entities
# =============================================================================


@pytest.fixture
def dealership_preference(db, dealership):
    """A preference linked to the test dealership."""
    return DealershipPreferenceFactory(dealer_id=dealership)


@pytest.fixture
def dealership_inventory(db, dealership, car_model):
    """An inventory record linked to the test dealership."""
    return DealershipInventoryFactory(dealer_id=dealership, car_model_id=car_model, quantity=10)


@pytest.fixture
def dealership_supplier(db, dealership, car_model):
    """A supplier link linked to the test dealership."""
    return DealershipSupplierFactory(dealer_id=dealership, car_model_id=car_model)


@pytest.fixture
def dealership_promo(db, dealership):
    """A promotion linked to the test dealership."""
    return DealershipPromoFactory(dealer=dealership)


@pytest.fixture
def dealership_promo_model(db, dealership_promo, car_model):
    """A promo-model link."""
    return DealershipPromoModelFactory(promo=dealership_promo, car_model=car_model)


@pytest.fixture
def dealership_sale(db, dealership):
    """A sale record linked to the test dealership."""
    return DealershipSaleFactory(dealership=dealership)


# =============================================================================
# API clients
# =============================================================================


@pytest.fixture
def dealership_api_client(api_client, dealership_user):
    """An API client authenticated as dealership_user."""
    api_client.force_authenticate(user=dealership_user)
    return api_client


@pytest.fixture
def other_dealership_api_client(api_client, other_dealership_user):
    """An API client authenticated as other_dealership_user."""
    api_client.force_authenticate(user=other_dealership_user)
    return api_client


@pytest.fixture
def buyer_api_client(api_client, buyer_user):
    """An API client authenticated as buyer_user."""
    api_client.force_authenticate(user=buyer_user)
    return api_client
