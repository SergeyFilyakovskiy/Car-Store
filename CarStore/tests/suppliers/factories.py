"""
Factory Boy factories for the suppliers application.
"""

from datetime import timedelta

import factory
from django.contrib.gis.geos import Point
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.faker import Faker
from suppliers.models import (
    Supplier,
    SupplierCar,
    SupplierLoyaltyDiscount,
    SupplierPromo,
    SupplierPromoModel,
)
from tests.accounts.factories import UserFactory
from tests.cars.factories import CarModelFactory


class SupplierFactory(factory.django.DjangoModelFactory):
    """Factory for creating suppliers."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Supplier

    name = Sequence(lambda n: f"Supplier_{n}")
    country = Faker("country_code")
    location = LazyFunction(lambda: Point(0, 0))
    founded_year = Faker("year")
    description = Faker("text", max_nb_chars=200)
    account_id = SubFactory(UserFactory, role="supplier")


class SupplierCarFactory(factory.django.DjangoModelFactory):
    """Factory for creating supplier car offers."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SupplierCar

    supplier_id = SubFactory(SupplierFactory)
    car_model_id = SubFactory(CarModelFactory)
    base_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    stock_quantity = Faker("random_int", min=0, max=100)


class SupplierLoyaltyDiscountFactory(factory.django.DjangoModelFactory):
    """Factory for creating supplier loyalty discounts."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SupplierLoyaltyDiscount

    supplier_id = SubFactory(SupplierFactory)
    # Requires dealers.factories.DealershipFactory
    dealer_id = SubFactory("dealers.factories.DealershipFactory")
    discount_pct = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    min_purchases = Faker("random_int", min=1, max=50)


class SupplierPromoFactory(factory.django.DjangoModelFactory):
    """Factory for creating supplier promotions."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SupplierPromo

    supplier = SubFactory(SupplierFactory)
    name = Sequence(lambda n: f"SupplierPromo_{n}")
    description = Faker("text", max_nb_chars=100)
    discount_pct = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    start_date = Faker("date_this_year", before_today=True)
    end_date = LazyAttribute(lambda o: o.start_date + timedelta(days=30))


class SupplierPromoModelFactory(factory.django.DjangoModelFactory):
    """Factory for linking supplier promos to car models."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SupplierPromoModel

    promo = SubFactory(SupplierPromoFactory)
    car_model = SubFactory(CarModelFactory)
