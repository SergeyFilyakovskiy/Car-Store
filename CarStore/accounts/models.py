from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Класс сущностей пользователей,
    содержет в себе общую для каждого
    пользоваетеля информацию
    """

    ROLES = (
        ("buyer", "Покупатель"),
        ("supplier", "Поставщик"),
        ("dealership", "Автосалон"),
        ("admin", "Администратор"),
    )

    role = models.CharField(
        max_length=20, choices=ROLES, default="buyer", verbose_name="Роль"
    )
