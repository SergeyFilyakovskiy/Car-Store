"""
Fixtures for the deals application tests.
"""

from datetime import timedelta

import pytest
from tests.deals.factories import (
    OfferFactory,
    PurchaseHistoryFactory,
    TransactionFactory,
)
from django.utils import timezone


@pytest.fixture
def offer(db, buyer_user, car_model):
    """Creates a test offer."""
    return OfferFactory(
        buyer=buyer_user.buyer,
        car_model=car_model,
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def transaction(db, buyer_user, dealership, supplier, car_model, offer):
    """Creates a test transaction."""
    return TransactionFactory(
        buyer=buyer_user.buyer,
        dealership=dealership,
        supplier=supplier,
        car_model=car_model,
        offer=offer,
    )


@pytest.fixture
def purchase_history(db, buyer_user, dealership, car_model, offer, transaction):
    """Creates a test purchase history record."""
    return PurchaseHistoryFactory(
        buyer=buyer_user.buyer,
        dealership=dealership,
        car_model=car_model,
        offer=offer,
        transaction=transaction,
    )
