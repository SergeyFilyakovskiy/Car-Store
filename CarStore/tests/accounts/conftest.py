"""
Фикстуры для тестов приложения accounts.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from tests.accounts.factories import BuyerFactory, UserFactory


@pytest.fixture
def user_factory():
    """Returns the UserFactory for creating users in tests."""
    return UserFactory


@pytest.fixture
def buyer_factory():
    """Returns a BuyerFactory for creating profiles in tests."""
    return BuyerFactory


@pytest.fixture
def buyer_user(db):
    """
    Creates a user with the 'buyer' role and an associated 'Buyer' profile.
    Used in buyer profile tests.
    """
    buyer = BuyerFactory(
        user__username="buyer_user",
        user__email="buyer@example.com",
        user__role="buyer",
        balance=1000.00,
        country="USA",
    )
    return buyer.user


@pytest.fixture
def buyer_profile(buyer_user):
    """Returns the Buyer profile for the user buyer_user."""
    return buyer_user.buyer


@pytest.fixture
def supplier_user(db):
    """Creates a user with the supplier role."""
    user = UserFactory(
        username="supplier_user",
        email="supplier@example.com",
        role="supplier",
    )
    return user


@pytest.fixture
def admin_user(db):
    """Creates a user with the admin role."""
    user = UserFactory(
        username="admin_user",
        email="admin@example.com",
        role="admin",
    )
    return user


@pytest.fixture
def anonymous_request():
    """Creates a mock request with an unauthenticated user."""
    from unittest.mock import Mock

    request = Mock()
    request.user = AnonymousUser()
    return request


@pytest.fixture
def authenticated_request(buyer_user):
    """Creates a mock request with an authenticated user."""
    from unittest.mock import Mock

    request = Mock()
    request.user = buyer_user
    return request
