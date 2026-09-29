from config import settings
from core.enums import StatusEnum
from core.models import BaseModel
from django.core.validators import MinValueValidator
from django.db import models


class Offer(BaseModel):
    """
    A purchase intent: the creator wants to buy `quantity` cars of `car_model`.

    The creator's role defines who may accept the offer:
        buyer      -> offer is addressed to dealerships
        dealership -> offer is addressed to suppliers
    """

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_offers",
        verbose_name="Creator",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Car model",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Quantity",
    )
    max_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Max price per unit",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusEnum.choices,
        default=StatusEnum.PENDING,
        verbose_name="Status",
    )
    expires_at = models.DateTimeField(verbose_name="Expires at")


class PurchaseHistory(BaseModel):
    """Stores completed buyer purchases: the deal context.

    Attributes:
        id: Unique history record identifier.
        buyer: Buyer who made the purchase.
        dealership: Dealership where the purchase was made.
        car_model: Purchased car model.
        offer: Related offer, if any.
        transaction: Related money transaction (from the accounts ledger).
        price_paid: Final paid price in USD.
        cost_price: Dealership's cost price in USD.
        purchased_at: Purchase timestamp.
    """

    buyer = models.ForeignKey(
        "accounts.Buyer",
        on_delete=models.CASCADE,
        related_name="purchase_history",
        verbose_name="Buyer",
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
    offer = models.OneToOneField(
        "deals.Offer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_history",
        verbose_name="Offer",
    )
    transaction = models.OneToOneField(
        "accounts.Transaction",
        on_delete=models.PROTECT,
        related_name="purchase_history",
        verbose_name="Transaction",
    )
    price_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Price paid",
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Cost price",
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Purchased at")

    class Meta:  # type: ignore
        verbose_name = "Purchase history"
        verbose_name_plural = "Purchase histories"
        ordering = ["-purchased_at"]

    def __str__(self) -> str:
        return f"{self.buyer} - {self.car_model} ({self.price_paid} USD)"


class OfferLog(BaseModel):
    """Audit of the processing of an incoming buyer offer."""

    offer = models.ForeignKey(
        "deals.Offer",
        on_delete=models.CASCADE,
        related_name="logs",
    )
    run_id = models.UUIDField(db_index=True)
    step = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    reason = models.CharField(max_length=255, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    class Meta:  # type: ignore
        verbose_name = "Offer log"
        verbose_name_plural = "Offer logs"
        indexes = [
            models.Index(fields=["offer", "created_at"]),
            models.Index(fields=["run_id", "created_at"]),
        ]


class SupplyHistory(BaseModel):
    """Purchases made by the salon from the supplier (salon → supplier).

    Analogous to PurchaseHistory, but for the salon-to-supplier direction.
    Used to count the number of purchases when calculating
    loyalty (SupplierLoyaltyDiscount.min_purchases).
    """

    dealership = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="supply_history",
        verbose_name="Dealership",
    )
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="supply_history",
        verbose_name="Supplier",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="supply_history",
        verbose_name="Car model",
    )
    offer = models.OneToOneField(
        "deals.Offer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supply_history",
        verbose_name="Offer",
    )
    transaction = models.OneToOneField(
        "accounts.Transaction",
        on_delete=models.PROTECT,
        related_name="supply_history",
        verbose_name="Transaction",
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantity")
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Unit price"
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Total price"
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Purchased at")

    class Meta:  # type: ignore
        verbose_name = "Supply history"
        verbose_name_plural = "Supply histories"
        ordering = ["-purchased_at"]
        indexes = [
            models.Index(fields=["dealership", "supplier"]),
        ]

    def __str__(self) -> str:
        return f"{self.dealership} ← {self.supplier} ({self.total_price} USD)"
