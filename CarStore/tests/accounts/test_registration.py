"""
Tests for the user registration endpoint.
Extracted from the legacy test_auth.py.
"""

from typing import Any

import pytest
from accounts.models import User
from django.urls import reverse

REGISTER_URL = "register"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestRegistration:
    """Tests for the RegisterAPIView endpoint."""

    def test_register_success(self, api_client):
        """Successful registration should return 201 and create an active user."""
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "buyer",
        }

        response = api_client.post(reverse(REGISTER_URL), payload, format="json")

        assert response.status_code == 201, _data(response)

        user = User.objects.get(username="newuser")
        assert user.is_active is True
        assert user.role == "buyer"

    def test_register_user_starts_unverified(self, api_client):
        """A freshly registered user must not have a verified email."""
        payload = {
            "username": "unverified",
            "email": "unverified@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "buyer",
        }

        api_client.post(reverse(REGISTER_URL), payload, format="json")

        user = User.objects.get(username="unverified")
        assert user.is_verifyed is False

    def test_register_password_mismatch(self, api_client):
        """Mismatching passwords should return 400."""
        payload = {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "StrongPass123!",
            "password2": "DifferentPass123!",
            "role": "buyer",
        }

        response = api_client.post(reverse(REGISTER_URL), payload, format="json")

        assert response.status_code == 400
        assert "password" in _data(response)

    def test_register_weak_password(self, api_client):
        """A weak password should fail Django validators."""
        payload = {
            "username": "weak",
            "email": "weak@example.com",
            "password": "123",
            "password2": "123",
            "role": "buyer",
        }

        response = api_client.post(reverse(REGISTER_URL), payload, format="json")

        assert response.status_code == 400

    def test_register_duplicate_email(self, api_client, buyer_user):
        """Registration with an existing email should return 400."""
        payload = {
            "username": "duplicate",
            "email": buyer_user.email,
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "buyer",
        }

        response = api_client.post(reverse(REGISTER_URL), payload, format="json")

        assert response.status_code == 400
        assert "email" in _data(response)
