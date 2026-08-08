"""
Fixtures for the dealers application tests.
"""

import pytest
from dealers.factories import (
    DealershipFactory,
    DealershipInventoryFactory,
    DealershipPreferenceFactory,
    DealershipPromoFactory,
    DealershipSaleFactory,
    DealershipSupplierFactory,
)


@pytest.fixture
def dealership_user(db):
    """Creates a user with the 'dealership' role."""
    from accounts.factories import UserFactory

    return UserFactory(
        role="dealership", username="dealer_user", email="dealer@example.com"
    )


@pytest.fixture
def dealership(db, dealership_user):
    """Creates a dealership owned by dealership_user."""
    return DealershipFactory(account_id=dealership_user, name="Test Dealership")


@pytest.fixture
def dealership_preference(db, dealership):
    """Creates a preference linked to the test dealership."""
    return DealershipPreferenceFactory(dealer_id=dealership)


@pytest.fixture
def dealership_inventory(db, dealership):
    """Creates an inventory record linked to the test dealership."""
    return DealershipInventoryFactory(dealer_id=dealership, quantity=10)


@pytest.fixture
def dealership_supplier(db, dealership):
    """Creates a supplier link linked to the test dealership."""
    return DealershipSupplierFactory(dealer_id=dealership)


@pytest.fixture
def dealership_promo(db, dealership):
    """Creates a promotion linked to the test dealership."""
    return DealershipPromoFactory(dealer=dealership)


@pytest.fixture
def dealership_sale(db, dealership):
    """Creates a sale record linked to the test dealership."""
    return DealershipSaleFactory(dealership=dealership)


@pytest.fixture
def other_dealership_user(db):
    """Creates a different user with the 'dealership' role (for negative tests)."""
    from accounts.factories import UserFactory

    return UserFactory(
        role="dealership", username="other_dealer", email="other@example.com"
    )


@pytest.fixture
def other_dealership(db, other_dealership_user):
    """Creates a dealership owned by other_dealership_user."""
    return DealershipFactory(account_id=other_dealership_user, name="Other Dealership")
