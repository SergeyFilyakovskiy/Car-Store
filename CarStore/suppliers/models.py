from config.settings import AUTH_USER_MODEL
from core.models import BaseModel
from django.contrib.gis.db import models


class Supplier(BaseModel):
    """
    Represents a car supplier.

    Attributes:
        id: Unique supplier identifier.
        name: Supplier name.
        country: Supplier country.
        location: Supplier geographic location as a point.
        founded_year: Year the supplier was founded.
        description: Free-form supplier description.
    """

    name = models.CharField(max_length=150, unique=True, verbose_name="Supplier name")
    country = models.CharField(max_length=56, verbose_name="Country")
    location = models.PointField(verbose_name="Location")
    founded_year = models.SmallIntegerField(verbose_name="Founded year")
    description = models.TextField(verbose_name="Description")
    account_id = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:  # type: ignore
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SupplierCar(BaseModel):
    """
    Represents a car model offered by a supplier.

    Attributes:
        id: Unique record identifier.
        supplier_id: Related supplier.
        car_model_id: Related car model.
        base_price: Base supplier price in USD.
        stock_quantity: Number of cars available in stock.
    """

    supplier_id = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="cars",
        verbose_name="Supplier",
    )
    car_model_id = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="supplier_offers",
        verbose_name="Car model",
    )
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Base price",
    )
    stock_quantity = models.IntegerField(default=0, verbose_name="Stock quantity")

    class Meta:  # type: ignore
        verbose_name = "Supplier car"
        verbose_name_plural = "Supplier cars"
        ordering = ["supplier_id", "car_model_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["supplier_id", "car_model_id"],
                name="unique_supplier_car_model",
            )
        ]

    def __str__(self) -> str:
        return f"{self.supplier_id.name} - {self.car_model_id}"


class SupplierLoyaltyDiscount(BaseModel):
    """
    Represents a supplier discount for a dealership.

    Attributes:
        id: Unique discount identifier.
        supplier_id: Related supplier.
        dealer_id: Related dealership.
        discount_pct: Discount percentage.
        min_purchases: Minimum number of purchases required to apply the discount.
    """

    supplier_id = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="loyalty_discounts",
        verbose_name="Supplier",
    )
    dealer_id = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="supplier_discounts",
        verbose_name="Dealership",
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Discount percent",
    )
    min_purchases = models.IntegerField(verbose_name="Minimum purchases")

    class Meta:  # type: ignore
        verbose_name = "Supplier loyalty discount"
        verbose_name_plural = "Supplier loyalty discounts"
        ordering = ["supplier_id", "dealer_id", "min_purchases"]
        constraints = [
            models.UniqueConstraint(
                fields=["supplier_id", "dealer_id"],
                name="unique_supplier_dealer_discount",
            )
        ]

    def __str__(self) -> str:
        return f"{self.supplier_id.name} → {self.dealer_id.name} ({self.discount_pct}%)"


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

    promo = models.ForeignKey(
        "suppliers.SupplierPromo",
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
