"""
Tests for the direct JWT obtain endpoint (CustomTokenObtainPairView).
Note: the primary production flow is the two-step OTP login
(see test_login_otp.py). This endpoint is kept for compatibility.
"""

from typing import Any

import pytest
from django.urls import reverse

TOKEN_URL = "token-obtain-pair"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestTokenObtain:
    """Tests for the CustomTokenObtainPairView endpoint."""

    def test_token_obtain_success(self, api_client, buyer_user):
        """Valid credentials should return 200 with tokens and custom claims."""
        buyer_user.is_active = True
        buyer_user.save(update_fields=["is_active"])

        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        response = api_client.post(reverse(TOKEN_URL), payload, format="json")

        assert response.status_code == 200, _data(response)
        assert "access" in _data(response)
        assert "refresh" in _data(response)

        # Custom user claims in the response body
        assert _data(response)["user"]["username"] == buyer_user.username
        assert _data(response)["user"]["role"] == buyer_user.role
        assert _data(response)["user"]["email"] == buyer_user.email

    def test_token_obtain_invalid_credentials(self, api_client, buyer_user):
        """Wrong password should return 401."""
        payload = {"username": buyer_user.username, "password": "WrongPassword123!"}

        response = api_client.post(reverse(TOKEN_URL), payload, format="json")

        assert response.status_code == 401

    def test_token_obtain_inactive_user(self, api_client, buyer_user):
        """An inactive user should receive 401."""
        buyer_user.is_active = False
        buyer_user.save(update_fields=["is_active"])

        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        response = api_client.post(reverse(TOKEN_URL), payload, format="json")

        assert response.status_code == 401
