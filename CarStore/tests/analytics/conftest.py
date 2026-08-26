"""
Fixtures for the analytics application tests.
"""

import pytest
from tests.analytics.factories import SalesStatisticsFactory


@pytest.fixture
def sales_statistics(db, dealership):
    """Creates sales statistics for the test dealership."""
    return SalesStatisticsFactory(dealership=dealership)


@pytest.fixture
def other_sales_statistics(db, other_dealership):
    """Creates sales statistics for another dealership."""
    return SalesStatisticsFactory(dealership=other_dealership)
