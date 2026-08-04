from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from core.models import BaseModel
from django.db import models


class CarBrand(BaseModel):
    """
    Represents a car manufacturer brand.

    Stores basic information about a car brand, including its name and country
    of origin. This model is used as a parent entity for car models.

    Attributes:
        id (UUID): Unique identifier of the brand.
        name (str): Brand name. Must be unique.
        country (str): Country of origin for the brand.

    Example:
        >>> brand = CarBrand.objects.create(name="BMW", country="Germany")

    Notes:
        - This model is a reference table for car models.
        - Brand names should be unique across the database.
    """

    name = models.CharField(max_length=80, unique=True, verbose_name="Brand name")
    country = models.CharField(max_length=56, verbose_name="Country of origin")

    class Meta:  # type: ignore
        verbose_name = "Car brand"
        verbose_name_plural = "Car brands"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CarModel(BaseModel):
    """
    Represents a specific car model.

    Stores the core technical and classification data for a car model, including
    its brand, body type, fuel type, transmission, drivetrain, engine volume,
    horsepower, and production year range. This model is used throughout the
    system for dealership inventory, supplier offers, and buyer preferences.

    Attributes:
        id (UUID): Unique identifier of the car model.
        brand_id (CarBrand): Foreign key to the car brand.
        name (str): Model name.
        body_type (str): Body type classification.
        fuel_type (str): Fuel type classification.
        transmission (str): Transmission type.
        drive_type (str): Drivetrain type.
        engine_volume (Decimal): Engine displacement in liters.
        horsepower (int | None): Engine power in horsepower.
        year_form (int | None): First production year.
        year_to (int | None): Last production year.

    Example:
        >>> model = CarModel.objects.create(
        ...     brand_id=brand,
        ...     name="X5",
        ...     body_type="SUV",
        ...     fuel_type="Petrol",
        ...     transmission="Automatic",
        ...     drive_type="AWD",
        ...     engine_volume=3.0,
        ...     horsepower=340,
        ...     year_form=2018,
        ...     year_to=2024
        ... )

    Notes:
        - The available values for body_type, fuel_type, transmission, and drive_type
          are taken from the corresponding enums in core.enums.
        - This model is the main car reference entity used by other apps.
    """

    brand = models.ForeignKey(
        "cars.CarBrand",
        on_delete=models.CASCADE,
        related_name="models",
        verbose_name="Brand",
    )
    name = models.CharField(max_length=100, verbose_name="Model name")
    body_type = models.CharField(
        max_length=20, choices=BodyTypesEnum.choices, verbose_name="Body type"
    )
    fuel_type = models.CharField(
        max_length=20, choices=FuelTypeEnum.choices, verbose_name="Fuel type"
    )
    transmission = models.CharField(
        max_length=10, choices=TransmissionTypeEnum.choices, verbose_name="Transmission"
    )
    drive_type = models.CharField(
        max_length=10, choices=DriveTypeEnum.choices, verbose_name="Drive type"
    )
    engine_volume = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name="Engine volume",
    )
    horsepower = models.SmallIntegerField(
        null=True, blank=True, verbose_name="Horsepower"
    )
    year_form = models.SmallIntegerField(
        null=True, blank=True, verbose_name="Production from"
    )
    year_to = models.SmallIntegerField(
        null=True, blank=True, verbose_name="Production to"
    )

    class Meta:  # type: ignore
        verbose_name = "Car model"
        verbose_name_plural = "Car models"
        ordering = ["brand_id", "name"]

    def __str__(self) -> str:
        return f"{self.brand_id.name} {self.name}"
