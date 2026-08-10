"""
Factory Boy factories for the dealers application.
"""

from datetime import timedelta

import factory
from core.enums import (
    BodyTypesEnum,
    DriveTypeEnum,
    FuelTypeEnum,
    StatusEnum,
    TransmissionTypeEnum,
)
from dealers.models import (
    Dealership,
    DealershipInventory,
    DealershipPreference,
    DealershipPromo,
    DealershipPromoModel,
    DealershipSale,
    DealershipSupplier,
)
from django.contrib.gis.geos import Point
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.faker import Faker
from tests.accounts.factories import BuyerFactory, UserFactory
from tests.cars.factories import CarModelFactory
from tests.deals.factories import OfferFactory
from tests.suppliers.factories import SupplierFactory


class DealershipFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealerships."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Dealership

    name = Sequence(lambda n: f"Dealership_{n}")
    country = Faker("country_code")
    address = LazyFunction(lambda: Point(0, 0))
    balance = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    account_id = SubFactory(UserFactory, role="dealership")


class DealershipPreferenceFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealership preferences."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipPreference

    dealer_id = SubFactory(DealershipFactory)
    body_type = BodyTypesEnum.SEDAN.value
    fuel_type = FuelTypeEnum.PETROL.value
    transmission = TransmissionTypeEnum.AT.value
    drive_type = DriveTypeEnum.FWD.value
    min_hp = 100
    max_hp = 300
    min_price = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    max_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class DealershipInventoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealership inventory records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipInventory

    dealer_id = SubFactory(DealershipFactory)
    car_model_id = SubFactory(CarModelFactory)
    quantity = Faker("random_int", min=0, max=50)
    sale_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class DealershipSupplierFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealership best supplier links."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipSupplier

    dealer_id = SubFactory(DealershipFactory)
    supplier_id = SubFactory(SupplierFactory)
    car_model_id = SubFactory(CarModelFactory)
    best_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class DealershipPromoFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealership promotions."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipPromo

    dealer = SubFactory(DealershipFactory)
    name = Sequence(lambda n: f"Promo_{n}")
    description = Faker("text", max_nb_chars=100)
    discount_pct = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    start_date = Faker("date_this_year", before_today=True)
    end_date = LazyAttribute(lambda o: o.start_date + timedelta(days=30))


class DealershipPromoModelFactory(factory.django.DjangoModelFactory):
    """Factory for linking promos to car models."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipPromoModel

    promo = SubFactory(DealershipPromoFactory)
    car_model = SubFactory(CarModelFactory)


class DealershipSaleFactory(factory.django.DjangoModelFactory):
    """Factory for creating dealership sales records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipSale

    dealership = SubFactory(DealershipFactory)
    buyer = SubFactory(BuyerFactory)
    car_model = SubFactory(CarModelFactory)
    offer = SubFactory(OfferFactory, status=StatusEnum.COMPLETED.value)
    sale_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    discount_applied = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
