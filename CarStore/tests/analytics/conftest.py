"""
Fixtures for the analytics application tests.
Self-contained: does not import fixtures from tests/dealers/.
"""

import pytest
from dealers.models import Dealership
from django.contrib.gis.geos import Point

from tests.accounts.factories import UserFactory
from tests.analytics.factories import SalesStatisticsFactory


def _create_dealership(name: str, account) -> Dealership:
    """Create a dealership owned by the given user account."""
    return Dealership.objects.create(
        name=name,
        country="USA",
        address=Point(0, 0),
        account_id=account,
    )


@pytest.fixture
def buyer_user(db):
    """A user with the buyer role (used for wrong-role tests)."""
    return UserFactory(role="buyer")


@pytest.fixture
def dealership_owner(db):
    """A dealership-role user and the dealership they own."""
    user = UserFactory(role="dealership", username="analytics_owner")
    dealership = _create_dealership("Analytics Owner Dealer", user)
    return user, dealership


@pytest.fixture
def other_dealership_owner(db):
    """A second dealership owner for isolation tests."""
    user = UserFactory(role="dealership", username="analytics_other_owner")
    dealership = _create_dealership("Analytics Other Dealer", user)
    return user, dealership


@pytest.fixture
def sales_statistics(dealership_owner):
    """Sales statistics for the primary dealership."""
    _, dealership = dealership_owner
    return SalesStatisticsFactory(dealership=dealership)


@pytest.fixture
def other_sales_statistics(other_dealership_owner):
    """Sales statistics for the other dealership."""
    _, dealership = other_dealership_owner
    return SalesStatisticsFactory(dealership=dealership)
