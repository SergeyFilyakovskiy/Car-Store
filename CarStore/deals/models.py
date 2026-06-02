import uuid

from core.enums import StatusEnum
from core.models import BaseModel
from django.db import models


class Offer(BaseModel):
    """Represents a buyer offer for a specific car model.

    Attributes:
        id: Unique offer identifier.
        buyer: Buyer who created the offer.
        car_model: Requested car model.
        max_price: Maximum price the buyer is willing to pay.
        status: Current offer status.
        expires_at: Offer expiration timestamp.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    buyer = models.ForeignKey(
        "accounts.Buyer",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Buyer",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Car model",
    )
    max_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Maximum price",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusEnum.choices,
        default=StatusEnum.PENDING,
        verbose_name="Status",
    )
    expires_at = models.DateTimeField(verbose_name="Expires at")

    class Meta:  # type: ignore
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.buyer} → {self.car_model} ({self.max_price} USD)"


class Transaction(BaseModel):
    """Represents a money movement in the system.

    Attributes:
        id: Unique transaction identifier.
        transaction_type: Type of transaction.
        amount: Transaction amount in USD.
        buyer: Buyer involved in the transaction, if any.
        dealership: Dealership involved in the transaction, if any.
        supplier: Supplier involved in the transaction, if any.
        car_model: Car model involved in the transaction.
        offer: Related offer, if any.
        reason: Explanation for the transaction.
    """

    class TransactionType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name="Transaction type",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    buyer = models.ForeignKey(
        "accounts.Buyer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name="Buyer",
    )
    dealership = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name="Dealership",
    )
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name="Supplier",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Car model",
    )
    offer = models.OneToOneField(
        "deals.Offer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transaction",
        verbose_name="Offer",
    )
    reason = models.TextField(blank=True, verbose_name="Reason")

    class Meta:  # type: ignore
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.amount} USD"


class PurchaseHistory(BaseModel):
    """Stores completed buyer purchases for reporting and analytics.

    Attributes:
        id: Unique history record identifier.
        buyer: Buyer who made the purchase.
        offer: Related offer.
        transaction: Related transaction.
        dealership: Dealership where the purchase was made.
        car_model: Purchased car model.
        price_paid: Final paid price in USD.
        purchased_at: Purchase timestamp.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    buyer = models.ForeignKey(
        "accounts.Buyer",
        on_delete=models.CASCADE,
        related_name="purchase_history",
        verbose_name="Buyer",
    )
    offer = models.OneToOneField(
        "deals.Offer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_history",
        verbose_name="Offer",
    )
    transaction = models.OneToOneField(
        "deals.Transaction",
        on_delete=models.CASCADE,
        related_name="purchase_history",
        verbose_name="Transaction",
    )
    dealership = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="purchase_history",
        verbose_name="Dealership",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="purchase_history",
        verbose_name="Car model",
    )
    price_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Price paid",
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Purchased at")

    class Meta:  # type: ignore
        verbose_name = "Purchase history"
        verbose_name_plural = "Purchase histories"
        ordering = ["-purchased_at"]

    def __str__(self) -> str:
        return f"{self.buyer} - {self.car_model} ({self.price_paid} USD)"
