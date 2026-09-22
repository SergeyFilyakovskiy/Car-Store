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
