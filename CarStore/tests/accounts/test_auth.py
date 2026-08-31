"""
Tests for authentication endpoints: Registration and JWT Token Obtain.
"""

from typing import cast

import pytest
from accounts.models import User
from django.urls import reverse
from rest_framework.response import Response


@pytest.mark.django_db
@pytest.mark.fast
class TestRegistration:
    """Tests for the RegisterAPIView endpoint."""

    def test_register_success(self, api_client):
        """Successful registration should return 201 and create an inactive user."""
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
        assert user.is_active is True
        assert user.role == "buyer"

    def test_register_password_mismatch(self, api_client):
        """Registration with mismatching passwords should return 400."""
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

    def test_register_weak_password(self, api_client):
        """Registration with a weak password should fail Django validators."""
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

    def test_register_duplicate_email(self, api_client, buyer_user):
        """Registration with an existing email should return 400."""
        payload = {
            "username": "duplicate",
            "email": buyer_user.email,
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "buyer",
        }

        response = cast(
            Response, api_client.post(reverse("register"), payload, format="json")
        )

        assert response.status_code == 400
        assert "email" in response.data  # pyright: ignore[reportOperatorIssue]


@pytest.mark.django_db
@pytest.mark.fast
class TestTokenObtain:
    """Tests for the CustomTokenObtainPairView endpoint."""

    def test_token_obtain_success(self, api_client, buyer_user):
        """Obtaining a token with valid credentials should return 200 with custom claims."""
        # Ensure user is active for login
        buyer_user.is_active = True
        buyer_user.save()

        payload = {
            "username": buyer_user.username,
            "password": "StrongPass123!",
        }

        response = cast(
            Response,
            api_client.post(reverse("token-obtain-pair"), payload, format="json"),
        )

        assert response.status_code == 200, response.data
        assert "access" in response.data  # pyright: ignore[reportOperatorIssue]
        assert "refresh" in response.data  # pyright: ignore[reportOperatorIssue]

        # Check custom user data in response
        assert "user" in response.data  # pyright: ignore[reportOperatorIssue]
        assert response.data["user"]["username"] == buyer_user.username  # pyright: ignore[reportOptionalSubscript]
        assert response.data["user"]["role"] == buyer_user.role  # pyright: ignore[reportOptionalSubscript]
        assert response.data["user"]["email"] == buyer_user.email  # pyright: ignore[reportOptionalSubscript]

    def test_token_obtain_invalid_credentials(self, api_client, buyer_user):
        """Obtaining a token with wrong password should return 401."""
        payload = {
            "username": buyer_user.username,
            "password": "WrongPassword123!",
        }

        response = cast(
            Response,
            api_client.post(reverse("token-obtain-pair"), payload, format="json"),
        )

        assert response.status_code == 401

    def test_token_obtain_inactive_user(self, api_client, buyer_user):
        """Obtaining a token for an inactive user should return 401."""
        buyer_user.is_active = False
        buyer_user.save()

        payload = {
            "username": buyer_user.username,
            "password": "StrongPass123!",
        }

        response = cast(
            Response,
            api_client.post(reverse("token-obtain-pair"), payload, format="json"),
        )

        assert response.status_code == 401
