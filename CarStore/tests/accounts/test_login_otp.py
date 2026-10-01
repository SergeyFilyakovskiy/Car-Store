"""
Tests for the two-step OTP login flow:
    Step 1: api_login_view      -> verify password, send OTP, return pending_token
    Step 2: api_verify_otp_view -> verify OTP, return JWT tokens
"""

from typing import Any
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse

# ---------------------------------------------------------------------------
# URL names — adjust these if your accounts/urls.py uses different names.
# ---------------------------------------------------------------------------
LOGIN_URL = "login"
VERIFY_OTP_URL = "verify_otp"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload to avoid repetitive ignores."""
    return response.data  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure a clean cache for every test in this module."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
@pytest.mark.fast
class TestApiLoginView:
    """Tests for Step 1: password verification + OTP dispatch."""

    def test_login_success_returns_pending_token(self, api_client, buyer_user):
        """Valid credentials should return 200 and a pending_token."""
        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        with patch("accounts.views.generate_and_send_otp") as mock_send:
            response = api_client.post(reverse(LOGIN_URL), payload, format="json")

        assert response.status_code == 200, _data(response)
        assert _data(response)["pending_token"] == f"pending_{buyer_user.id}"
        assert "message" in _data(response)
        mock_send.assert_called_once_with(buyer_user)

    def test_login_stores_pending_token_in_cache(self, api_client, buyer_user):
        """The pending_token should map to the user id in the cache."""
        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        with patch("accounts.views.generate_and_send_otp"):
            api_client.post(reverse(LOGIN_URL), payload, format="json")

        assert cache.get(f"pending_{buyer_user.id}") == buyer_user.id

    def test_login_invalid_credentials_returns_401(self, api_client, buyer_user):
        """Wrong password should return 401 and not send an OTP."""
        payload = {"username": buyer_user.username, "password": "WrongPass123!"}

        with patch("accounts.views.generate_and_send_otp") as mock_send:
            response = api_client.post(reverse(LOGIN_URL), payload, format="json")

        assert response.status_code == 401
        mock_send.assert_not_called()

    def test_login_inactive_user_returns_401(self, api_client, buyer_user):
        """An inactive user cannot authenticate."""
        buyer_user.is_active = False
        buyer_user.save(update_fields=["is_active"])

        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        with patch("accounts.views.generate_and_send_otp") as mock_send:
            response = api_client.post(reverse(LOGIN_URL), payload, format="json")

        assert response.status_code == 401
        mock_send.assert_not_called()

    def test_login_missing_fields_returns_400(self, api_client):
        """Missing username/password should fail serializer validation."""
        response = api_client.post(reverse(LOGIN_URL), {}, format="json")

        assert response.status_code == 400

    def test_login_rate_limit_returns_429(self, api_client, buyer_user):
        """A second login within the cooldown window should return 429."""
        cache.set(f"otp_cooldown_{buyer_user.id}", True, timeout=60)

        payload = {"username": buyer_user.username, "password": "StrongPass123!"}

        with patch("accounts.views.generate_and_send_otp") as mock_send:
            response = api_client.post(reverse(LOGIN_URL), payload, format="json")

        assert response.status_code == 429
        mock_send.assert_not_called()


@pytest.mark.django_db
@pytest.mark.fast
class TestApiVerifyOtpView:
    """Tests for Step 2: OTP verification + JWT issuance."""

    def _seed_pending_token(self, user) -> str:
        """Put a valid pending_token into the cache and return it."""
        pending_token = f"pending_{user.id}"
        cache.set(pending_token, user.id, timeout=300)
        return pending_token

    def test_verify_success_returns_tokens(self, api_client, buyer_user):
        """A valid OTP should return 200 with access/refresh tokens and user data."""
        pending_token = self._seed_pending_token(buyer_user)
        payload = {"pending_token": pending_token, "otp": "123456"}

        with patch("accounts.views.verify_otp", return_value=(True, None)) as mock_verify:
            response = api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert response.status_code == 200, _data(response)
        assert "access" in _data(response)
        assert "refresh" in _data(response)
        assert _data(response)["user"]["username"] == buyer_user.username
        mock_verify.assert_called_once_with(buyer_user, "123456")

    def test_verify_clears_pending_token_on_success(self, api_client, buyer_user):
        """After a successful verification the pending_token must be removed."""
        pending_token = self._seed_pending_token(buyer_user)
        payload = {"pending_token": pending_token, "otp": "123456"}

        with patch("accounts.views.verify_otp", return_value=(True, None)):
            api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert cache.get(pending_token) is None

    def test_verify_missing_fields_returns_400(self, api_client):
        """Both pending_token and otp are required."""
        response = api_client.post(reverse(VERIFY_OTP_URL), {}, format="json")

        assert response.status_code == 400

    def test_verify_invalid_pending_token_returns_400(self, api_client):
        """An unknown pending_token should return 400."""
        payload = {"pending_token": "pending_unknown", "otp": "123456"}

        response = api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert response.status_code == 400

    def test_verify_expired_pending_token_returns_400(self, api_client, buyer_user):
        """An expired pending_token (not in cache) should return 400."""
        payload = {"pending_token": f"pending_{buyer_user.id}", "otp": "123456"}
        # Note: token is NOT seeded into the cache.

        response = api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert response.status_code == 400

    def test_verify_wrong_otp_returns_401(self, api_client, buyer_user):
        """An invalid OTP should return 401 and keep the pending_token alive."""
        pending_token = self._seed_pending_token(buyer_user)
        payload = {"pending_token": pending_token, "otp": "000000"}

        with patch(
            "accounts.views.verify_otp", return_value=(False, "Invalid OTP")
        ):
            response = api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert response.status_code == 401
        assert _data(response)["error"] == "Invalid OTP"
        # pending_token should survive a failed attempt
        assert cache.get(pending_token) == buyer_user.id

    def test_verify_user_not_found_returns_404(self, api_client, buyer_user):
        """If the user was deleted between steps, return 404."""
        pending_token = self._seed_pending_token(buyer_user)
        user_id = buyer_user.id
        buyer_user.delete()

        payload = {"pending_token": pending_token, "otp": "123456"}

        response = api_client.post(reverse(VERIFY_OTP_URL), payload, format="json")

        assert response.status_code == 404

@pytest.mark.django_db
@pytest.mark.fast
class TestFullOtpLoginFlow:
    """End-to-end OTP login without mocking verify_otp.
    This test fails if the otp_code_/otp_key cache-key mismatch returns."""

    def test_full_login_flow_with_real_otp(self, api_client, buyer_user, settings):
        """Password login -> OTP from cache -> JWT tokens."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        # Step 1: request the OTP
        login_payload = {
            "username": buyer_user.username,
            "password": "StrongPass123!",
        }
        login_response = api_client.post(
            reverse(LOGIN_URL), login_payload, format="json"
        )

        assert login_response.status_code == 200, _data(login_response)
        pending_token = _data(login_response)["pending_token"]

        # Read the real OTP straight from the cache
        real_otp = cache.get(f"otp_code_{buyer_user.id}")
        assert real_otp is not None, "OTP was not stored under otp_code_<id>"

        # Step 2: verify the real OTP
        verify_payload = {"pending_token": pending_token, "otp": real_otp}
        verify_response = api_client.post(
            reverse(VERIFY_OTP_URL), verify_payload, format="json"
        )

        assert verify_response.status_code == 200, _data(verify_response)
        assert "access" in _data(verify_response)
        assert "refresh" in _data(verify_response)
