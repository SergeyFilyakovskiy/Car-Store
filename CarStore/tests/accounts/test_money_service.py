"""
Tests for MoneyService and BalanceTopUpService business logic.
These are the core money-movement tests and must be exhaustive.
"""

from decimal import Decimal

import pytest
from accounts.exceptions import (
    BalanceTopUpError,
    InsufficientBalanceError,
    TopUpInvalidStatusError,
)
from accounts.models import Entry, Transaction
from accounts.services import BalanceTopUpService, MoneyService


@pytest.mark.django_db
@pytest.mark.fast
class TestMoneyServiceTransfer:
    """Tests for MoneyService.transfer (debit + credit between two users)."""

    def test_transfer_moves_money(self, user_factory):
        """A successful transfer debits sender and credits receiver."""
        sender = user_factory(balance=Decimal("100.00"))
        receiver = user_factory(balance=Decimal("0.00"))

        txn = MoneyService.transfer(
            from_user_id=sender.id,
            to_user_id=receiver.id,
            amount=Decimal("30.00"),
            idempotency_key="transfer-1",
        )

        sender.refresh_from_db()
        receiver.refresh_from_db()

        assert sender.balance == Decimal("70.00")
        assert receiver.balance == Decimal("30.00")
        assert txn.status == Transaction.Status.COMPLETED

    def test_transfer_creates_two_entries(self, user_factory):
        """A transfer must create exactly one DEBIT and one CREDIT entry."""
        sender = user_factory(balance=Decimal("100.00"))
        receiver = user_factory(balance=Decimal("0.00"))

        txn = MoneyService.transfer(
            from_user_id=sender.id,
            to_user_id=receiver.id,
            amount=Decimal("30.00"),
            idempotency_key="transfer-entries",
        )

        entries = Entry.objects.filter(transaction=txn)
        assert entries.count() == 2
        assert entries.filter(type=Entry.EntryType.DEBIT, user=sender).count() == 1
        assert entries.filter(type=Entry.EntryType.CREDIT, user=receiver).count() == 1

    def test_transfer_is_idempotent(self, user_factory):
        """Replaying the same idempotency_key must not move money twice."""
        sender = user_factory(balance=Decimal("100.00"))
        receiver = user_factory(balance=Decimal("0.00"))

        kwargs = {
            "from_user_id": sender.id,
            "to_user_id": receiver.id,
            "amount": Decimal("30.00"),
            "idempotency_key": "transfer-idem",
        }

        MoneyService.transfer(**kwargs)
        MoneyService.transfer(**kwargs)  # replay

        sender.refresh_from_db()
        receiver.refresh_from_db()

        # Money moved exactly once
        assert sender.balance == Decimal("70.00")
        assert receiver.balance == Decimal("30.00")
        # Only one transaction exists for this key
        assert Transaction.objects.filter(idempotency_key="transfer-idem").count() == 1

    def test_transfer_insufficient_balance(self, user_factory):
        """A transfer larger than the sender balance must fail."""
        sender = user_factory(balance=Decimal("10.00"))
        receiver = user_factory(balance=Decimal("0.00"))

        with pytest.raises(InsufficientBalanceError):
            MoneyService.transfer(
                from_user_id=sender.id,
                to_user_id=receiver.id,
                amount=Decimal("50.00"),
                idempotency_key="transfer-insufficient",
            )

        sender.refresh_from_db()
        receiver.refresh_from_db()
        assert sender.balance == Decimal("10.00")
        assert receiver.balance == Decimal("0.00")

    def test_transfer_zero_amount_rejected(self, user_factory):
        """Zero or negative amounts must be rejected."""
        sender = user_factory(balance=Decimal("100.00"))
        receiver = user_factory(balance=Decimal("0.00"))

        with pytest.raises(BalanceTopUpError):
            MoneyService.transfer(
                from_user_id=sender.id,
                to_user_id=receiver.id,
                amount=Decimal("0"),
                idempotency_key="transfer-zero",
            )


@pytest.mark.django_db
@pytest.mark.fast
class TestMoneyServiceCredit:
    """Tests for MoneyService.credit (money enters the system)."""

    def test_credit_adds_money(self, user_factory):
        """Credit increases the user balance."""
        user = user_factory(balance=Decimal("0.00"))

        txn = MoneyService.credit(
            user_id=user.id,
            amount=Decimal("50.00"),
            idempotency_key="credit-1",
        )

        user.refresh_from_db()
        assert user.balance == Decimal("50.00")
        assert txn.status == Transaction.Status.COMPLETED

    def test_credit_is_idempotent(self, user_factory):
        """Replaying the same credit must not double the balance."""
        user = user_factory(balance=Decimal("0.00"))

        kwargs = {
            "user_id": user.id,
            "amount": Decimal("50.00"),
            "idempotency_key": "credit-idem",
        }

        MoneyService.credit(**kwargs)
        MoneyService.credit(**kwargs)  # replay

        user.refresh_from_db()
        assert user.balance == Decimal("50.00")


@pytest.mark.django_db
@pytest.mark.fast
class TestBalanceTopUpService:
    """Tests for the BalanceTopUpService lifecycle."""

    def test_create_topup_request_is_pending(self, buyer_user):
        """A new topup request starts in PENDING status."""
        topup = BalanceTopUpService.create_topup_request(
            user=buyer_user.id,
            amount=Decimal("100.00"),
            payment_method="CARD",
        )

        assert topup.status == "PENDING"
        assert topup.amount == Decimal("100.00")

    def test_confirm_topup_credits_balance(self, buyer_user):
        """Confirming a topup credits the user balance."""
        topup = BalanceTopUpService.create_topup_request(
            user=buyer_user.id,
            amount=Decimal("100.00"),
            payment_method="CARD",
        )
        initial_balance = buyer_user.balance

        confirmed = BalanceTopUpService.confirm_topup(
            topup_id=topup.id,
            external_id="ext-123",
        )

        buyer_user.refresh_from_db()
        assert confirmed.status == "COMPLETED"
        assert buyer_user.balance == initial_balance + Decimal("100.00")

    def test_confirm_topup_is_idempotent(self, buyer_user):
        """Replaying confirm with the same external_id must not double-credit."""
        topup = BalanceTopUpService.create_topup_request(
            user=buyer_user.id,
            amount=Decimal("100.00"),
            payment_method="CARD",
        )
        initial_balance = buyer_user.balance

        BalanceTopUpService.confirm_topup(topup_id=topup.id, external_id="ext-123")
        BalanceTopUpService.confirm_topup(topup_id=topup.id, external_id="ext-123")

        buyer_user.refresh_from_db()
        assert buyer_user.balance == initial_balance + Decimal("100.00")

    def test_cancel_topup_from_pending(self, buyer_user):
        """A pending topup can be cancelled."""
        topup = BalanceTopUpService.create_topup_request(
            user=buyer_user.id,
            amount=Decimal("100.00"),
            payment_method="CARD",
        )

        cancelled = BalanceTopUpService.cancel_topup(topup.id)
        assert cancelled.status == "CANCELLED"

    def test_cancel_completed_topup_fails(self, buyer_user):
        """Cancelling a non-pending topup must raise."""
        topup = BalanceTopUpService.create_topup_request(
            user=buyer_user.id,
            amount=Decimal("100.00"),
            payment_method="CARD",
        )
        BalanceTopUpService.confirm_topup(topup_id=topup.id, external_id="ext-123")

        with pytest.raises(TopUpInvalidStatusError):
            BalanceTopUpService.cancel_topup(topup.id)
