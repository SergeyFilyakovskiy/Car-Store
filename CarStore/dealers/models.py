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
        choices=[(e.value, e.value) for e in BodyTypesEnum], verbose_name="Body type"
    )
    fuel_type = models.CharField(
        choices=[(e.value, e.value) for e in FuelTypeEnum], verbose_name="Fuel type"
    )
    transmission = models.CharField(
        choices=[(e.value, e.value) for e in TransmissionTypeEnum],
        verbose_name="Transmission",
    )
    drive_type = models.CharField(
        choices=[(e.value, e.value) for e in DriveTypeEnum], verbose_name="Drive type"
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
