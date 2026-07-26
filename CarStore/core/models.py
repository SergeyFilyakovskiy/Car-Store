import uuid

from django.db import models


# Create your models here.
class BaseModel(models.Model):
    """
    Abstract class for ORM models

    :id:         UUID
    :created_at: datetime
    :updated_at: datetime
    :is_active:  bool
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
