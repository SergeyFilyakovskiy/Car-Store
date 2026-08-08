"""
Factory Boy factories for the dealers application.
"""

from datetime import timedelta

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
from factory.django import DjangoModelFactory
from factory.faker import Faker


class DealershipFactory(DjangoModelFactory):
    """Factory for creating dealerships."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Dealership

    name = Sequence(lambda n: f"Dealership_{n}")
    country = Faker("country_code")
    address = LazyFunction(lambda: Point(0, 0))
    balance = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    # Requires accounts.factories.UserFactory to exist
    account_id = SubFactory("accounts.factories.UserFactory", role="dealership")


class DealershipPreferenceFactory(DjangoModelFactory):
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


class DealershipInventoryFactory(DjangoModelFactory):
    """Factory for creating dealership inventory records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipInventory

    dealer_id = SubFactory(DealershipFactory)
    # Requires cars.factories.CarModelFactory to exist
    car_model_id = SubFactory("cars.factories.CarModelFactory")
    quantity = Faker("random_int", min=0, max=50)
    sale_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class DealershipSupplierFactory(DjangoModelFactory):
    """Factory for creating dealership best supplier links."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipSupplier

    dealer_id = SubFactory(DealershipFactory)
    # Requires suppliers.factories.SupplierFactory to exist
    supplier_id = SubFactory("suppliers.factories.SupplierFactory")
    car_model_id = SubFactory("cars.factories.CarModelFactory")
    best_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class DealershipPromoFactory(DjangoModelFactory):
    """Factory for creating dealership promotions."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipPromo

    dealer = SubFactory(DealershipFactory)
    name = Sequence(lambda n: f"Promo_{n}")
    description = Faker("text", max_nb_chars=100)
    discount_pct = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    start_date = Faker("date_this_year", before_today=True)
    end_date = LazyAttribute(lambda o: o.start_date + timedelta(days=30))


class DealershipPromoModelFactory(DjangoModelFactory):
    """Factory for linking promos to car models."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipPromoModel

    promo = SubFactory(DealershipPromoFactory)
    car_model = SubFactory("cars.factories.CarModelFactory")


class DealershipSaleFactory(DjangoModelFactory):
    """Factory for creating dealership sales records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = DealershipSale

    dealership = SubFactory(DealershipFactory)
    # Requires accounts.factories.BuyerFactory to exist
    buyer = SubFactory("accounts.factories.BuyerFactory")
    car_model = SubFactory("cars.factories.CarModelFactory")
    # Requires deals.factories.OfferFactory to exist
    offer = SubFactory(
        "deals.factories.OfferFactory", status=StatusEnum.COMPLETED.value
    )
    sale_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    discount_applied = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
