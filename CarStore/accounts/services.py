"""Users balance top up services."""

from decimal import Decimal
from uuid import UUID

from deals.exceptions import InsufficientBalanceError
from django.db import transaction

from .exceptions import (
    BalanceTopUpError,
    TopUpAlreadyProcessedError,
    TopUpInvalidStatusError,
)
from .models import BalanceTopUp, User


class BalanceService:
    @staticmethod
    def debit(user: User, amount: Decimal) -> None:
        """
        Write off from the balance.
        The user object must already be blocked.
        """
        if user.balance < amount:
            raise InsufficientBalanceError(f"Need {amount}, but has {user.balance}")
        user.balance -= amount
        user.save(update_fields=["balance"])

    @staticmethod
    def credit(user: User, amount: Decimal) -> None:
        """
        Credit to the balance.
        The user object must already be blocked.
        """
        user.balance += amount
        user.save(update_fields=["balance"])


class BalanceTopUpService:
    """
    Service for work with users balance topups

    All methods are atomic and protected against re-processing (idempotent).
    """

    @staticmethod
    @transaction.atomic
    def create_topup_request(
        user: User,
        amount: Decimal,
        payment_method: str,
    ) -> BalanceTopUp:
        """
        Creates a replenishment request.
        """

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

        user = User.objects.select_for_update().get(user=topup.user)

        BalanceService.credit(user, topup.amount)

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

        # еще можно было бы добавить модель истории измений баланса

        return topup

    @staticmethod
    @transaction.atomic
    def fail_topup(
        topup_id: UUID,
        reason: str = "",
    ) -> BalanceTopUp:
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
        topup.save(
            update_fields=["status"],
        )
        return topup
