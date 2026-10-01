
import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient

from tests.accounts.factories import (
    AdminUserFactory,
    BalanceTopUpFactory,
    BuyerFactory,
    DealershipUserFactory,
    SupplierUserFactory,
    UserFactory,
)


# ---- Users ----


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
    buyer = BuyerFactory(
        user__username="buyer_user",
        user__email="buyer@example.com",
        user__role="buyer",
        user__balance=1000.00,
        country="USA",
    )
    return buyer.user


@pytest.fixture
def buyer_profile(buyer_user):
    return buyer_user.buyer


@pytest.fixture
def supplier_user(db):
    return SupplierUserFactory(
        username="supplier_user",
        email="supplier@example.com",
    )


@pytest.fixture
def dealership_user(db):
    return DealershipUserFactory(
        username="dealership_user",
        email="dealership@example.com",
    )


@pytest.fixture
def admin_user(db):
    return AdminUserFactory(
        username="admin_user",
        email="admin@example.com",
    )


@pytest.fixture
def unverified_user(db):
    return UserFactory(
        username="unverified_user",
        email="unverified@example.com",
        is_verifyed=False,
    )


# ---- Requests ----


@pytest.fixture
def anonymous_request():
    from unittest.mock import Mock

    request = Mock()
    request.user = AnonymousUser()
    return request


@pytest.fixture
def authenticated_request(buyer_user):
    from unittest.mock import Mock

    request = Mock()
    request.user = buyer_user
    return request


# ---- API clients ----


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def buyer_api_client(api_client, buyer_user):
    api_client.force_authenticate(user=buyer_user)
    return api_client


@pytest.fixture
def supplier_api_client(api_client, supplier_user):
    api_client.force_authenticate(user=supplier_user)
    return api_client


@pytest.fixture
def dealership_api_client(api_client, dealership_user):
    api_client.force_authenticate(user=dealership_user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


# ---- TopUp ----


@pytest.fixture
def balance_topup_factory():
    return BalanceTopUpFactory


@pytest.fixture
def pending_topup(buyer_user):
    return BalanceTopUpFactory(user=buyer_user, status=BalanceTopUpFactory._meta.model.Status.PENDING)
