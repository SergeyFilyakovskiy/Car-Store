import uuid

from config import settings
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from core.models import BaseModel
from django.contrib.gis.db import models


class Dealership(BaseModel):
    """
    Dealership - the main entity for modeling car sales.

    Stores information about the dealership, including location, balance, owner,
    and linkage to user account. Used for automatic car purchasing from suppliers
    based on preferences and sales history.

    Attributes:
        id (UUID): Unique dealership identifier (UUID4).
        name (str): Dealership name, must be unique (max_length=200).
        country (str): Country where dealership is located (ISO code, max_length=56).
        address (Point): Geolocation of dealership (PostGIS PointField).
        balance (Decimal): Current balance for purchasing cars (14 digits, 2 decimal places).
        account_id (User): Dealership owner (ForeignKey to AUTH_USER_MODEL).

    Examples:
        >>> dealer = Dealership.objects.create(
        ...     name="BMW Center Minsk",
        ...     country="BY",
        ...     balance=1000000.00
        ... )
        >>> dealer.account_id = user
        >>> dealer.save()

    Note:
        - Uses PostGIS for geolocation storage (PointField).
        - Balance is always in USD (US Dollars).
        - Soft deletion via is_active field in BaseModel.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=200, unique=True, verbose_name="Dealership name")
    country = models.CharField(max_length=56, verbose_name="Country")
    address = models.PointField(verbose_name="Address (coordinates)")
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Balance (USD)"
    )
    account_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dealerships",
        verbose_name="Owner",
    )

    class Meta:  # type: ignore
        verbose_name = "Dealership"
        verbose_name_plural = "Dealerships"
        ordering = ["name"]


class DealershipPreference(BaseModel):
    """
    Dealership preferences for car characteristics used in purchasing.

    Defines criteria for car selection in automatic purchasing via Celery.
    The system analyzes demand based on sales history and selects cars matching
    these preferences.

    Attributes:
        id (UUID): Unique preference identifier (UUID4).
        dealer_id (Dealership): Dealership that owns these preferences.
        body_type (str): Body type (from BodyTypesEnum).
        fuel_type (str): Fuel type (from FuelTypeEnum).
        transmission (str): Transmission type (from TransmissionTypeEnum).
        drive_type (str): Drive type (from DriveTypeEnum).
        min_hp (int): Minimum engine power (horsepower).
        max_hp (int): Maximum engine power (horsepower).
        min_price (Decimal): Minimum purchase price (USD).
        max_price (Decimal): Maximum purchase price (USD).

    Examples:
        >>> preference = DealershipPreference.objects.create(
        ...     dealer_id=dealer,
        ...     body_type=BodyTypesEnum.SUV.value,
        ...     fuel_type=FuelTypeEnum.PETROL.value,
        ...     transmission=TransmissionTypeEnum.AUTO.value,
        ...     drive_type=DriveTypeEnum.ALL.value,
        ...     min_hp=200,
        ...     max_hp=400,
        ...     min_price=30000,
        ...     max_price=80000
        ... )

    Note:
        - Used for automatic car selection during purchasing.
        - Multiple preferences can exist for one dealership.
        - Celery task analyzes demand and purchases cars matching these criteria.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealer_id = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="preferences",
        verbose_name="Dealership",
    )
    body_type = models.CharField(
        max_length=20,
        choices=BodyTypesEnum.choices,
        verbose_name="Body type",
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelTypeEnum.choices,
        verbose_name="Fuel type",
    )
    transmission = models.CharField(
        max_length=10,
        choices=TransmissionTypeEnum.choices,
        verbose_name="Transmission",
    )
    drive_type = models.CharField(
        max_length=10,
        choices=DriveTypeEnum.choices,
        verbose_name="Drive type",
    )
    min_hp = models.SmallIntegerField(verbose_name="Min. horsepower")
    max_hp = models.SmallIntegerField(verbose_name="Max. horsepower")
    min_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Min. price (USD)"
    )
    max_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Max. price (USD)"
    )

    class Meta:  # type: ignore
        verbose_name = "Dealership preference"
        verbose_name_plural = "Dealership preferences"
        unique_together = ["dealer_id", "body_type", "fuel_type"]
        ordering = ["dealer_id", "body_type"]


class DealershipInventory(BaseModel):
    """
    Dealership inventory - cars in stock at the dealership.

    Stores information about available cars, their quantity, and sale price.
    Used for tracking inventory and automatic replenishment via Celery.

    Attributes:
        id (UUID): Unique inventory record identifier (UUID4).
        dealer_id (Dealership): Dealership that owns this car.
        car_model_id (CarModel): Car model (ForeignKey to cars.CarModel).
        quantity (int): Number of cars of this model in stock.
        sale_price (Decimal): Sale price for customers (USD).

    Examples:
        >>> inventory = DealershipInventory.objects.create(
        ...     dealer_id=dealer,
        ...     car_model_id=car_model,
        ...     quantity=5,
        ...     sale_price=45000.00
        ... )
        >>> # Update quantity after sale
        >>> inventory.quantity -= 1
        >>> inventory.save()

    Note:
        - Unique combination: dealer_id + car_model_id (one record per model).
        - quantity = 0 means car is temporarily out of stock.
        - Celery task checks inventory and purchases when stock is low (< 2 days demand).
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealer_id = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="inventory",
        verbose_name="Dealership",
    )
    car_model_id = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="dealer_inventory",
        verbose_name="Car model",
    )
    quantity = models.IntegerField(default=0, verbose_name="Quantity in stock")
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Sale price (USD)"
    )

    class Meta:  # type: ignore
        verbose_name = "Car in stock"
        verbose_name_plural = "Cars in stock"
        unique_together = ["dealer_id", "car_model_id"]
        ordering = ["dealer_id", "car_model_id"]


class DealershipSupplier(BaseModel):
    """
    Link between dealership and suppliers for specific car model with best price.

    Stores information about the best supplier for each car model considering
    promotions, discounts, and base prices. Automatically updated via Celery task
    (hourly) to select the most profitable supplier.

    Attributes:
        id (UUID): Unique record identifier (UUID4).
        dealer_id (Dealership): Dealership for which supplier is selected.
        supplier_id (Supplier): Car supplier (ForeignKey).
        car_model_id (CarModel): Car model (ForeignKey).
        best_price (Decimal): Best price from this supplier (USD) including promotions.

    Examples:
        >>> best_supplier = DealershipSupplier.objects.create(
        ...     dealer_id=dealer,
        ...     supplier_id=supplier,
        ...     car_model_id=car_model,
        ...     best_price=35000.00
        ... )
        >>> # Celery task updates best_price when promotions change
        >>> best_supplier.best_price = 33500.00  # After 5% promotion
        >>> best_supplier.save()

    Note:
        - Unique combination: dealer_id + supplier_id + car_model_id.
        - best_price includes base price + supplier discounts + promotions.
        - Celery task (hourly) updates list of best suppliers.
        - During purchasing (every 10 min), system selects supplier with best price.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealer_id = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="best_suppliers",
        verbose_name="Dealership",
    )
    supplier_id = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="dealer_contracts",
        verbose_name="Supplier",
    )
    car_model_id = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="dealer_suppliers",
        verbose_name="Car model",
    )
    best_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Best price (USD)"
    )

    class Meta:  # type: ignore
        verbose_name = "Best supplier for dealership"
        verbose_name_plural = "Best suppliers for dealerships"
        unique_together = ["dealer_id", "supplier_id", "car_model_id"]
        ordering = ["dealer_id", "car_model_id", "best_price"]


class DealershipPromo(BaseModel):
    """
    Represents a promotional campaign created by a dealership.

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
    """
    Links a dealership promotion to a car model.

    Attributes:
        id: Unique relation identifier.
        promo: Related dealership promotion.
        car_model: Related car model.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    promo = models.ForeignKey(
        "dealers.DealershipPromo",
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


class DealershipSale(BaseModel):
    """Represents a completed sale from a dealership to a buyer.

    Attributes:
        id: Unique sale identifier.
        dealership: Related dealership.
        buyer: Related buyer.
        car_model: Related car model.
        offer: Related purchase offer.
        promo: Applied dealership promotion, if any.
        sale_price: Final sale price in USD.
        discount_applied: Applied discount percentage.
        sold_at: Date when the sale was completed.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealership = models.ForeignKey(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Dealership",
    )
    buyer = models.ForeignKey(
        "accounts.Buyer",
        on_delete=models.CASCADE,
        related_name="purchases",
        verbose_name="Buyer",
    )
    car_model = models.ForeignKey(
        "cars.CarModel",
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Car model",
    )
    offer = models.ForeignKey(
        "deals.Offer",
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Offer",
    )
    promo = models.ForeignKey(
        "deals.DealershipPromo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
        verbose_name="Dealership promotion",
    )
    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Sale price",
    )
    discount_applied = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Discount applied",
    )
    sold_at = models.DateTimeField(auto_now_add=True, verbose_name="Sold at")

    class Meta:  # type: ignore
        verbose_name = "Dealership sale"
        verbose_name_plural = "Dealership sales"
        ordering = ["-sold_at", "-id"]

    def __str__(self) -> str:
        return f"{self.dealership.name} → {self.buyer} ({self.sale_price} USD)"
