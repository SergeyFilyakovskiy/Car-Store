import uuid

from config import settings
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from core.models import BaseModel
from django.contrib.gis.db import models


class Dealership(BaseModel):
    """
    Dealer ORM model
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=56)
    address = models.PointField()
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    account_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class DealershipPreference(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    dealer_id = models.ForeignKey("dealers.Dealership", on_delete=models.CASCADE)
    body_type = models.CharField(choices=[(e.value, e.value) for e in BodyTypesEnum])
    fuel_type = models.CharField(choices=[(e.value, e.value) for e in FuelTypeEnum])
    transmission = models.CharField(
        choices=[(e.value, e.value) for e in TransmissionTypeEnum]
    )
    drive_type = models.CharField(choices=[(e.value, e.value) for e in DriveTypeEnum])
    min_hp = models.SmallIntegerField()
    max_hp = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=2)
    max_price = models.DecimalField(max_digits=12, decimal_places=2)
