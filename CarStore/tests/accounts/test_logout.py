"""
Tests for the logout endpoint (refresh token blacklisting).
"""

from typing import Any
from unittest.mock import patch

import pytest
from django.urls import reverse

LOGOUT_URL = "logout"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.mark.django_db
@pytest.mark.fast
class TestLogout:
    """Tests for the api_logout_view endpoint."""

    def test_logout_unauthenticated_returns_401(self, api_client):
        """An unauthenticated request must be rejected."""
        response = api_client.post(reverse(LOGOUT_URL), {}, format="json")

        assert response.status_code == 401

    def test_logout_without_refresh_token_returns_400(self, buyer_api_client):
        """Missing refresh token should return 400."""
        response = buyer_api_client.post(reverse(LOGOUT_URL), {}, format="json")

        assert response.status_code == 400

    def test_logout_success_blacklists_token(self, buyer_api_client, buyer_user):
        """A valid refresh token should be blacklisted and return 200."""
        from rest_framework_simplejwt.tokens import RefreshToken

        # Создаём реальный токен
        refresh = RefreshToken.for_user(buyer_user)

        with patch.object(RefreshToken, "blacklist") as mock_blacklist:
            response = buyer_api_client.post(
                reverse(LOGOUT_URL),
                {"refresh": str(refresh)},
                format="json",
            )

        assert response.status_code == 200
        mock_blacklist.assert_called_once()
