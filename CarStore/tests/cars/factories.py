"""
Factory Boy фабрики для моделей cars.
"""

import factory
from cars.models import CarBrand, CarModel
from core.enums import BodyTypesEnum, DriveTypeEnum, FuelTypeEnum, TransmissionTypeEnum
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker


class CarBrandFactory(factory.django.DjangoModelFactory):
    """A factory for creating automotive brands."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = CarBrand

    name = Sequence(lambda n: f"Brand_{n}")
    country = Faker("country")


class CarModelFactory(factory.django.DjangoModelFactory):
    """A factory for creating car models."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = CarModel

    brand = SubFactory(CarBrandFactory)
    name = Sequence(lambda n: f"Model_{n}")
    body_type = BodyTypesEnum.SEDAN.value
    fuel_type = FuelTypeEnum.PETROL.value
    transmission = TransmissionTypeEnum.AT.value
    drive_type = DriveTypeEnum.FWD.value
    engine_volume = Faker("pydecimal", left_digits=1, right_digits=1, positive=True)
    horsepower = Faker("random_int", min=100, max=500)
    year_form = Faker("random_int", min=2000, max=2020)
    year_to = Faker("random_int", min=2020, max=2026)
