import uuid

from config import settings
from core.enums import BodyTypesEnum, FuelTypeEnum
from core.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models


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

    role = models.CharField(
        max_length=20, choices=ROLES, default="buyer", verbose_name="Роль"
    )


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

    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.balance} USD)"
