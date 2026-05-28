import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


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
