"""
Tests for the email change flow: request, confirm, cancel.
Requires the email-change routes (Blocker 1).
"""

from typing import Any
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse

REQUEST_URL = "email-change-request"
CONFIRM_URL = "email-change-confirm"
CANCEL_URL = "email-change-cancel"


def _data(response) -> dict[str, Any]:
    """Typed accessor for response payload."""
    return response.data  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def clear_cache():
    """Clean cache between tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
@pytest.mark.fast
class TestRequestEmailChange:
    """Tests for POST /email/change/request/."""

    def test_request_email_change_success(self, buyer_api_client, buyer_user):
        """A valid request stores pending_email and sends OTP."""
        payload = {"email": "newemail@example.com"}

        with patch("accounts.views.generate_email_change_otp") as mock_send:
            response = buyer_api_client.post(
                reverse(REQUEST_URL), payload, format="json"
            )

        assert response.status_code == 200, _data(response)
        buyer_user.refresh_from_db()
        assert buyer_user.pending_email == "newemail@example.com"
        mock_send.assert_called_once_with(buyer_user)

    def test_request_same_email_returns_400(self, buyer_api_client, buyer_user):
        """Requesting the current email must fail."""
        payload = {"email": buyer_user.email}

        response = buyer_api_client.post(reverse(REQUEST_URL), payload, format="json")

        assert response.status_code == 400

    def test_request_existing_email_returns_400(self, buyer_api_client, supplier_user):
        """Requesting an email already in use must fail."""
        payload = {"email": supplier_user.email}

        response = buyer_api_client.post(reverse(REQUEST_URL), payload, format="json")

        assert response.status_code == 400

    def test_request_rate_limit_returns_429(self, buyer_api_client, buyer_user):
        """A second request within cooldown must return 429."""
        cache.set(f"email_change_cooldown_{buyer_user.id}", True, timeout=60)

        payload = {"email": "newemail@example.com"}

        with patch("accounts.views.generate_email_change_otp") as mock_send:
            response = buyer_api_client.post(
                reverse(REQUEST_URL), payload, format="json"
            )

        assert response.status_code == 429
        mock_send.assert_not_called()


@pytest.mark.django_db
@pytest.mark.fast
class TestConfirmEmailChange:
    """Tests for POST /email/change/confirm/."""

    def _request_pending(self, user, new_email="newemail@example.com"):
        """Helper: set a pending email on the user."""
        user.pending_email = new_email
        user.save(update_fields=["pending_email"])

    def test_confirm_success_changes_email(self, buyer_api_client, buyer_user):
        """A valid OTP swaps the email and clears pending_email."""
        self._request_pending(buyer_user)

        with patch(
            "accounts.views.verify_email_change_otp", return_value=(True, None)
        ):
            response = buyer_api_client.post(
                reverse(CONFIRM_URL), {"otp": "123456"}, format="json"
            )

        assert response.status_code == 200, _data(response)
        buyer_user.refresh_from_db()
        assert buyer_user.email == "newemail@example.com"
        assert buyer_user.pending_email is None

    def test_confirm_no_pending_returns_404(self, buyer_api_client):
        """Confirming without a pending email returns 404."""
        response = buyer_api_client.post(
            reverse(CONFIRM_URL), {"otp": "123456"}, format="json"
        )

        assert response.status_code == 404

    def test_confirm_wrong_otp_returns_400(self, buyer_api_client, buyer_user):
        """An invalid OTP returns 400 and keeps the old email."""
        self._request_pending(buyer_user)
        old_email = buyer_user.email

        with patch(
            "accounts.views.verify_email_change_otp",
            return_value=(False, "Invalid code."),
        ):
            response = buyer_api_client.post(
                reverse(CONFIRM_URL), {"otp": "000000"}, format="json"
            )

        assert response.status_code == 400
        buyer_user.refresh_from_db()
        assert buyer_user.email == old_email


@pytest.mark.django_db
@pytest.mark.fast
class TestCancelEmailChange:
    """Tests for POST /email/change/cancel/."""

    def test_cancel_clears_pending_email(self, buyer_api_client, buyer_user):
        """Cancelling removes the pending_email."""
        buyer_user.pending_email = "newemail@example.com"
        buyer_user.save(update_fields=["pending_email"])

        response = buyer_api_client.post(reverse(CANCEL_URL), {}, format="json")

        assert response.status_code == 200
        buyer_user.refresh_from_db()
        assert buyer_user.pending_email is None

    def test_cancel_without_pending_returns_400(self, buyer_api_client):
        """Cancelling with no pending email returns 400."""
        response = buyer_api_client.post(reverse(CANCEL_URL), {}, format="json")

        assert response.status_code == 400
