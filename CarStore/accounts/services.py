"""Users balance top up services."""

from decimal import Decimal

from deals.exceptions import InsufficientBalanceError
from django.db import transaction

from .models import User


class BalanceService:
    @staticmethod
    def debit(user: User, amount: Decimal) -> None:
        """Списать с баланса. Объект user должен быть уже заблокирован."""
        if user.balance < amount:
            raise InsufficientBalanceError(f"Need {amount}, but has {user.balance}")
        user.balance -= amount
        user.save(update_fields=["balance"])

    @staticmethod
    def credit(user: User, amount: Decimal) -> None:
        """Зачислить на баланс. Объект user должен быть уже заблокирован."""
        user.balance += amount
        user.save(update_fields=["balance"])


@transaction.atomic()
def top_up_balance(user: User):
    pass
