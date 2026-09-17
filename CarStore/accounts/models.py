import uuid
from decimal import Decimal

from config import settings
from core.enums import BodyTypesEnum, FuelTypeEnum
from core.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.db.models import Sum


class User(AbstractUser):
    """
    A user entity class,contains
    information common to each user
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ROLES = (
        ("buyer", "Buyer"),
        ("supplier", "Supplier"),
        ("dealership", "Dealership"),
        ("admin", "Administrator"),
    )
    email = models.EmailField(unique=True, verbose_name="Email")

    pending_email = models.EmailField(
        unique=True, verbose_name="Pending Email", null=True
    )

    role = models.CharField(
        max_length=20, choices=ROLES, default="buyer", verbose_name="Role"
    )

    is_verifyed = models.BooleanField(
        default=False, verbose_name="Email verification status"
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Balance (USD)",
    )

    def get_balance(self) -> Decimal:
        """
        Returns current balance based on all ledger entries.
        This is the single source of truth.
        """

        result = self.ledger_entries.aggregate(total=Sum("amount"))  # pyright: ignore[reportAttributeAccessIssue]
        return result["total"] or Decimal("0")

    def get_balance_history(self, limit: int = 50):
        """Returns recent balance history."""
        return self.ledger_entries.order_by("-created_at")[:limit]  # pyright: ignore[reportAttributeAccessIssue]


class Buyer(BaseModel):
    """Represents a buyer profile in the system.

    Attributes:
        id: Unique buyer identifier.
        user_id: Related authentication user.
        balance: Current buyer balance in USD.
        date_of_birth: Buyer date of birth.
        gender: Buyer gender.
        phone: Contact phone number.
        country: Buyer country.
        location: Buyer geographic location.
        preferred_body_type: Preferred car body type.
        preferred_fuel_type: Preferred car fuel type.
    """

    class GenderChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Balance"
    )
    date_of_birth = models.DateField(verbose_name="Date of birth")
    gender = models.CharField(
        max_length=1,
        choices=GenderChoices.choices,
        default=GenderChoices.MALE,
        verbose_name="Gender",
    )
    phone = models.CharField(max_length=30, verbose_name="Phone")
    country = models.CharField(max_length=56, verbose_name="Country")
    location = models.PointField(verbose_name="Location")
    preferred_body_type = models.CharField(
        max_length=50,
        choices=BodyTypesEnum.choices,
        verbose_name="Preferred body type",
    )
    preferred_fuel_type = models.CharField(
        max_length=50,
        choices=FuelTypeEnum.choices,
        verbose_name="Preferred fuel type",
    )

    class Meta:  # type: ignore
        verbose_name = "Buyer"
        verbose_name_plural = "Buyers"
        ordering = ["user"]

    def __str__(self) -> str:
        return f"{self.user} ({self.balance} USD)"


class BalanceTopUp(BaseModel):
    """User balance top-up."""

    class PaymentMethod(models.TextChoices):
        CARD = "CARD", "Card"
        CRYPTO = "CRYPTO", "Crypto"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="balance_topups",
    )

    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        verbose_name="Amount",
    )

    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, verbose_name="Payment Method"
    )

    external_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        unique=True,
        verbose_name="Tranaction ID payment system",
    )

    status = models.CharField(
        max_length=20,
        default=Status.PENDING,
        choices=Status.choices,
        verbose_name="Top up status",
    )

    payment_provider_response = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:  # type: ignore
        verbose_name = "Balance top up"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]


class LedgerEntry(BaseModel):
    """
    Universal ledger entry for all financial operations.
    Single source of truth for user balance.
    """

    class EntryType(models.TextChoices):
        TOP_UP = "TOP_UP", "Balance Top-up"
        PURCHASE = "PURCHASE", "Car Purchase (money out)"
        SALE = "SALE", "Car Sale (money in)"
        REFUND = "REFUND", "Refund"
        ADJUSTMENT = "ADJUSTMENT", "Manual Adjustment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
        verbose_name="User",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Amount",
    )

    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        verbose_name="Entry type",
    )

    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Balance after",
    )

    transaction = models.ForeignKey(
        "deals.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
        verbose_name="Related transaction",
    )

    topup = models.ForeignKey(
        "accounts.BalanceTopUp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
        verbose_name="Related top-up",
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = "Ledger entry"
        verbose_name_plural = "Ledger entries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username}: {self.amount} ({self.entry_type})"
