from typing import cast

import pytest
from accounts.models import Buyer, User
from core.enums import BodyTypesEnum, FuelTypeEnum
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_user(db):
    """Creates an active user (for profile tests)."""
    user = User.objects.create_user(
        username="testuser",
        password="StrongPass123!",
        email="test@example.com",
        role="buyer",
        is_active=True,
    )
    return user


@pytest.fixture
def buyer_profile(db, active_user):
    """Creates a buyer profile for the user."""
    buyer = Buyer.objects.create(
        user=active_user,
        balance=1000.00,
        date_of_birth="1990-01-01",
        gender="M",
        phone="+1234567890",
        country="USA",
        location=Point(-73.935242, 40.730610),
        preferred_body_type=BodyTypesEnum.SEDAN.value,
        preferred_fuel_type=FuelTypeEnum.PETROL.value,
    )
    return buyer


# ==================== Registration Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_register_success(api_client):
    """A successful registration should return 201."""
    payload = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "StrongPass123!",
        "password2": "StrongPass123!",
        "role": "buyer",
    }

    response = cast(
        Response, api_client.post(reverse("register"), payload, format="json")
    )

    assert response.status_code == 201, response.data
    assert User.objects.filter(username="newuser").exists()
    user = User.objects.get(username="newuser")
    assert user.is_active is False


@pytest.mark.django_db
@pytest.mark.fast
def test_register_password_mismatch(api_client):
    """Registration with mismatched passwords should return a 400."""
    payload = {
        "username": "mismatch",
        "email": "mismatch@example.com",
        "password": "StrongPass123!",
        "password2": "DifferentPass123!",
        "role": "buyer",
    }

    response = cast(
        Response, api_client.post(reverse("register"), payload, format="json")
    )

    assert response.status_code == 400
    assert "password" in response.data  # pyright: ignore[reportOperatorIssue]


@pytest.mark.django_db
@pytest.mark.fast
def test_register_weak_password(api_client):
    """Registration with a weak password should return a 400."""
    payload = {
        "username": "weak",
        "email": "weak@example.com",
        "password": "123",
        "password2": "123",
        "role": "buyer",
    }

    response = cast(
        Response, api_client.post(reverse("register"), payload, format="json")
    )

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.fast
def test_register_duplicate_email(api_client, active_user):
    """Registration with an existing email should return a 400 status code."""
    payload = {
        "username": "duplicate",
        "email": active_user.email,
        "password": "StrongPass123!",
        "password2": "StrongPass123!",
        "role": "buyer",
    }

    response = cast(
        Response, api_client.post(reverse("register"), payload, format="json")
    )

    assert response.status_code == 400


# ==================== Token Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_token_obtain_success(api_client, active_user):
    """Obtaining a token with valid data should return a 200 status code."""
    payload = {
        "username": "testuser",
        "password": "StrongPass123!",
    }

    response = cast(
        Response, api_client.post(reverse("token-obtain-pair"), payload, format="json")
    )

    assert response.status_code == 200, response.data
    assert "access" in response.data  # pyright: ignore[reportOperatorIssue]
    assert "refresh" in response.data  # pyright: ignore[reportOperatorIssue]
    assert "user" in response.data  # pyright: ignore[reportOperatorIssue]
    assert response.data["user"]["username"] == "testuser"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["user"]["role"] == "buyer"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_token_obtain_invalid_credentials(api_client, active_user):
    """Obtaining a token with an incorrect password should return a 401."""
    payload = {
        "username": "testuser",
        "password": "WrongPassword123!",
    }

    response = cast(
        Response, api_client.post(reverse("token-obtain-pair"), payload, format="json")
    )

    assert response.status_code == 401


# ==================== Buyer Profile Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_get_buyer_profile_success(api_client, active_user, buyer_profile):
    """Obtaining a buyer profile needs to work for the owner."""
    api_client.force_authenticate(user=active_user)

    response = cast(Response, api_client.get(reverse("buyer-profile")))

    assert response.status_code == 200, response.data
    assert response.data["user"]["username"] == "testuser"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["balance"] == "1000.00"  # pyright: ignore[reportOptionalSubscript]
    assert response.data["country"] == "USA"  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.django_db
@pytest.mark.fast
def test_get_buyer_profile_unauthenticated(api_client):
    """Retrieving the profile without authorization should return a 401."""
    response = cast(Response, api_client.get(reverse("buyer-profile")))

    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
def test_get_buyer_profile_no_profile(api_client, active_user):
    """Retrieving a profile without an existing Buyer should return a 404."""
    api_client.force_authenticate(user=active_user)
    # active_user не имеет связанного Buyer профиля

    response = cast(Response, api_client.get(reverse("buyer-profile")))

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.fast
def test_update_buyer_profile_success(api_client, active_user, buyer_profile):
    """Updating the buyer profile should work for the owner."""
    api_client.force_authenticate(user=active_user)

    payload = {
        "balance": 2000.00,
        "phone": "+9876543210",
        "country": "Canada",
    }

    response = cast(
        Response,
        api_client.patch(reverse("buyer-profile-update"), payload, format="json"),
    )

    assert response.status_code == 200, response.data
    buyer_profile.refresh_from_db()
    assert buyer_profile.balance == 2000.00
    assert buyer_profile.phone == "+9876543210"
    assert buyer_profile.country == "Canada"


@pytest.mark.django_db
@pytest.mark.fast
def test_update_buyer_profile_unauthenticated(api_client, buyer_profile):
    """Updating the profile without authorization should return a 401."""
    payload = {
        "balance": 9999.00,
    }

    response = cast(
        Response,
        api_client.patch(reverse("buyer-profile-update"), payload, format="json"),
    )

    assert response.status_code == 401


# ==================== Permissions Tests ====================


@pytest.mark.django_db
@pytest.mark.fast
def test_is_buyer_permission():
    """IsBuyer permission test."""
    from accounts.permissions import IsBuyer
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.get("/fake-url")

    # Unauthenticated user
    request.user = AnonymousUser()
    permission = IsBuyer()
    assert permission.has_permission(request, None) is False

    # User with the buyer role
    buyer_user = User(role="buyer")
    request.user = buyer_user
    assert permission.has_permission(request, None) is True

    # User with a different role
    supplier_user = User(role="supplier")
    request.user = supplier_user
    assert permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.fast
def test_is_owner_profile_permission(api_client, active_user, buyer_profile):
    """IsOwnerProfile permission test."""
    from accounts.permissions import IsOwnerProfile
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.get("/fake-url")
    request.user = active_user

    permission = IsOwnerProfile()

    # Profile owner
    assert permission.has_object_permission(request, None, buyer_profile) is True

    # Another user
    other_user = User.objects.create_user(
        username="other", password="StrongPass123!", email="other@example.com"
    )
    request.user = other_user
    assert permission.has_object_permission(request, None, buyer_profile) is False
