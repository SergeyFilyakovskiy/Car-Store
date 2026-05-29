import uuid

from config import settings
from core.models import BaseModel
from django.contrib.gis.db import models


class Dealership(BaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=56)
    address = models.PointField()
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    account_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
