import uuid

from django.db import models


# Create your models here.
class BaseModel(models.Model):
    """
    Абстрактный класс для ORM моделей

    :id:         UUID
    :created_at: datetime
    :updated_at: datetime
    :is_active:  bool
    """

    id = models.UUIDField(default=uuid.uuid4(), primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
