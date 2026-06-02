import uuid

from core.models import BaseModel
from django.db import models


class DealershipPromo(BaseModel):
    """Represents a promotional campaign created by a dealership.

    Attributes:
        id: Unique promotion identifier.
        dealer: Related dealership that owns the promotion.
        name: Promotion name.
        description: Promotion description.
        discount_pct: Discount percentage for eligible cars.
        start_date: Date when the promotion starts.
        end_date: Date when the promotion ends.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealer = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="promotions",
        verbose_name="Dealership",
    )
    name = models.CharField(max_length=200, verbose_name="Promotion name")
    description = models.TextField(blank=True, verbose_name="Description")
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Discount percent",
    )
    start_date = models.DateField(verbose_name="Start date")
    end_date = models.DateField(verbose_name="End date")

    class Meta:  # type: ignore
        verbose_name = "Dealership promotion"
        verbose_name_plural = "Dealership promotions"
        ordering = ["dealer", "start_date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.dealer.name})"


class DealershipPromoModel(BaseModel):
    """Links a dealership promotion to a car model.

    Attributes:
        id: Unique relation identifier.
        promo: Related dealership promotion.
        car_model: Related car model.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    promo = models.ForeignKey(
        "deals.DealershipPromo",
        on_delete=models.CASCADE,
        related_name="promo_models",
        verbose_name="Promotion",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="dealership_promo_links",
        verbose_name="Car model",
    )

    class Meta:  # type: ignore
        verbose_name = "Dealership promotion model"
        verbose_name_plural = "Dealership promotion models"
        constraints = [
            models.UniqueConstraint(
                fields=["promo", "car_model"],
                name="unique_dealership_promo_car_model",
            )
        ]

    def __str__(self) -> str:
        return f"{self.promo.name} → {self.car_model}"


class SupplierPromo(BaseModel):
    """Represents a promotional campaign created by a supplier.

    Attributes:
        id: Unique promotion identifier.
        supplier: Related supplier that owns the promotion.
        name: Promotion name.
        description: Promotion description.
        discount_pct: Discount percentage for eligible cars.
        start_date: Date when the promotion starts.
        end_date: Date when the promotion ends.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="promotions",
        verbose_name="Supplier",
    )
    name = models.CharField(max_length=150, verbose_name="Promotion name")
    description = models.TextField(blank=True, verbose_name="Description")
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Discount percent",
    )
    start_date = models.DateField(verbose_name="Start date")
    end_date = models.DateField(verbose_name="End date")

    class Meta:  # type: ignore
        verbose_name = "Supplier promotion"
        verbose_name_plural = "Supplier promotions"
        ordering = ["supplier", "start_date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.supplier.name})"


class SupplierPromoModel(BaseModel):
    """Links a supplier promotion to a car model.

    Attributes:
        id: Unique relation identifier.
        promo: Related supplier promotion.
        car_model: Related car model.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    promo = models.ForeignKey(
        "deals.SupplierPromo",
        on_delete=models.CASCADE,
        related_name="promo_models",
        verbose_name="Promotion",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="supplier_promo_links",
        verbose_name="Car model",
    )

    class Meta:  # type: ignore
        verbose_name = "Supplier promotion model"
        verbose_name_plural = "Supplier promotion models"
        constraints = [
            models.UniqueConstraint(
                fields=["promo", "car_model"],
                name="unique_supplier_promo_car_model",
            )
        ]

    def __str__(self) -> str:
        return f"{self.promo.name} → {self.car_model}"
