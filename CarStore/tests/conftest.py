"""
Shared fixtures for all project tests.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Creates an instance of APIClient for API testing."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """
    Creates an active user with the 'buyer' role.
    Used in most tests as the base user.
    """
    from accounts.models import User

    user = User.objects.create_user(
        username="testuser",
        password="StrongPass123!",
        email="test@example.com",
        role="buyer",
        is_active=True,
    )
    return user


@pytest.fixture
def api_client_with_user(api_client, authenticated_user):
    """
    Creates an APIClient with an authenticated user.
    Useful for tests that require authentication.
    """
    api_client.force_authenticate(user=authenticated_user)
    return api_client
