"""Users balance top up services."""

from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.db import transaction as db_transaction

from .exceptions import (
    BalanceTopUpError,
    InsufficientBalanceError,
    TopUpAlreadyProcessedError,
    TopUpInvalidStatusError,
)
from .models import BalanceTopUp, Entry, Transaction, User


class MoneyService:
    """Single entry point for all money movements."""

    @staticmethod
    def transfer(
        *,
        from_user_id,
        to_user_id,
        amount: Decimal,
        idempotency_key: str,
        description: str = "",
    ) -> Transaction:
        """Moves money between two users: DEBIT + CREDIT."""
        if amount <= 0:
            raise BalanceTopUpError("Amount must be positive")

        with db_transaction.atomic():
            txn, _ = Transaction.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={"description": description},
            )

        return MoneyService._run(
            txn,
            [
                (from_user_id, amount, Entry.EntryType.DEBIT),
                (to_user_id, amount, Entry.EntryType.CREDIT),
            ],
        )

    @staticmethod
    def credit(
        *, user_id, amount: Decimal, idempotency_key: str, description: str = ""
    ) -> Transaction:
        """Money enters the system from outside (payment provider)."""
        if amount <= 0:
            raise BalanceTopUpError("Amount must be positive")

        with db_transaction.atomic():
            txn, _ = Transaction.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={"description": description},
            )

        return MoneyService._run(txn, [(user_id, amount, Entry.EntryType.CREDIT)])

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _run(txn: Transaction, legs: list[tuple]) -> Transaction:
        if txn.status == Transaction.Status.COMPLETED:
            return txn  # idempotent replay: money already moved

        try:
            with db_transaction.atomic():
                MoneyService._execute_legs(txn, legs)
                txn.status = Transaction.Status.COMPLETED
                txn.save(update_fields=["status"])
        except Exception:
            Transaction.objects.filter(
                id=txn.id, status=Transaction.Status.PENDING
            ).update(status=Transaction.Status.FAILED)
            raise
        return txn

    @staticmethod
    def _execute_legs(txn: Transaction, legs: list[tuple]) -> None:
        user_ids = sorted({user_id for user_id, _, _ in legs})
        locked = {
            u.id: u for u in User.objects.select_for_update().filter(id__in=user_ids)
        }
        for user_id, amount, entry_type in legs:
            user = locked[user_id]
            if entry_type == Entry.EntryType.DEBIT:
                if user.balance < amount:
                    raise InsufficientBalanceError(
                        f"User {user_id} has {user.balance}, needs {amount}"
                    )
                user.balance -= amount
            else:
                user.balance += amount
            user.save(update_fields=["balance"])
            Entry.objects.create(
                transaction=txn,
                user=user,
                amount=amount,
                type=entry_type,
                balance_after=user.balance,
            )


class BalanceTopUpService:
    """
    Service for work with users balance topups.

    All methods are atomic and protected against re-processing (idempotent).
    """

    @staticmethod
    @transaction.atomic
    def create_topup_request(
        user: User,
        amount: Decimal,
        payment_method: str,
    ) -> BalanceTopUp:
        """Creates a replenishment request."""
        if amount <= 0:
            raise BalanceTopUpError("Amount must be positive")

        topup = BalanceTopUp.objects.create(
            user=user,
            amount=amount,
            payment_method=payment_method,
            status=BalanceTopUp.Status.PENDING,
        )
        return topup

    @staticmethod
    @transaction.atomic
    def confirm_topup(
        topup_id: UUID,
        external_id: str,
        provider_response: dict | None = None,
    ) -> BalanceTopUp:
        """
        Confirms the top-up and credits the funds.
        Called from the payment system's webhook.
        """
        topup = BalanceTopUp.objects.select_for_update().get(id=topup_id)

        if topup.status == BalanceTopUp.Status.COMPLETED:
            if topup.external_transaction_id != external_id:
                raise TopUpAlreadyProcessedError(
                    f"TopUp {topup_id} already completed with different external_id"
                )
            return topup

        if topup.status != BalanceTopUp.Status.PENDING:
            raise TopUpInvalidStatusError(
                f"TopUp {topup_id} has status {topup.status}, excepted PENDING"
            )

        # user = User.objects.select_for_update().get(id=topup.user_id)  # pyright: ignore[reportAttributeAccessIssue]

        # BalanceService.credit(
        #     user=user,
        #     amount=topup.amount,
        #     entry_type=LedgerEntry.EntryType.TOP_UP,
        #     description=f"Balance top-up via {topup.payment_method}",
        #     topup=topup,
        # )

        topup.status = BalanceTopUp.Status.COMPLETED
        topup.external_transaction_id = external_id
        topup.payment_provider_response = provider_response or {}
        topup.save(
            update_fields=[
                "status",
                "external_transaction_id",
                "payment_provider_response",
            ]
        )
        return topup

    @staticmethod
    @transaction.atomic
    def fail_topup(topup_id: UUID, reason: str = "") -> BalanceTopUp:
        """Mark TopUp as failed."""
        topup = BalanceTopUp.objects.select_for_update().get(id=topup_id)

        if topup.status != BalanceTopUp.Status.PENDING:
            raise TopUpInvalidStatusError(
                f"Cannot fail topup with status {topup.status}"
            )

        topup.status = BalanceTopUp.Status.FAILED
        topup.payment_provider_response = {"error": reason}
        topup.save(update_fields=["status", "payment_provider_response"])
        return topup

    @staticmethod
    @transaction.atomic
    def cancel_topup(topup_id: UUID) -> BalanceTopUp:
        """Cancel topup. For example - timeout."""
        topup = BalanceTopUp.objects.select_for_update().get(id=topup_id)

        if topup.status != BalanceTopUp.Status.PENDING:
            raise TopUpInvalidStatusError(
                f"Cannot cancel topup with status {topup.status}"
            )

        topup.status = BalanceTopUp.Status.CANCELLED
        topup.save(update_fields=["status"])
        return topup
