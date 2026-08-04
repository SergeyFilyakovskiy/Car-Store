"""
Factory Boy фабрики для моделей accounts.
Позволяют быстро создавать тестовые данные без boilerplate кода.
"""

import factory
from accounts.models import Buyer, User
from core.enums import BodyTypesEnum, FuelTypeEnum
from factory.declarations import (
    LazyAttribute,
    PostGenerationMethodCall,
    Sequence,
    SubFactory,
)
from factory.faker import Faker


class UserFactory(factory.django.DjangoModelFactory):
    """User creation factory."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = User
        skip_postgeneration_save = True

    username = Sequence(lambda n: f"user_{n}")
    email = LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = PostGenerationMethodCall("set_password", "StrongPass123!")
    role = "buyer"
    is_active = True


class BuyerFactory(factory.django.DjangoModelFactory):
    """Factory for creating customer profiles."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Buyer

    user = SubFactory(UserFactory)
    balance = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    date_of_birth = Faker("date_of_birth", minimum_age=18, maximum_age=65)
    gender = "M"
    phone = Faker("phone_number")
    country = Faker("country")
    location = "POINT(0 0)"
    preferred_body_type = BodyTypesEnum.SEDAN.value
    preferred_fuel_type = FuelTypeEnum.PETROL.value
