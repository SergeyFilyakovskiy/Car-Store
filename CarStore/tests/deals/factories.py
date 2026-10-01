"""
Factory Boy factories for the deals application.
"""

from datetime import timedelta

import factory
from core.enums import StatusEnum
from deals.models import Offer, PurchaseHistory, SupplyHistory
from django.utils import timezone
from factory.declarations import LazyFunction, Sequence, SubFactory
from factory.faker import Faker

from tests.accounts.factories import BuyerFactory, TransactionFactory, UserFactory
from tests.cars.factories import CarModelFactory


class OfferFactory(factory.django.DjangoModelFactory):
    """Factory for creating offers."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Offer

    creator = SubFactory(UserFactory)
    car_model = SubFactory(CarModelFactory)
    quantity = 1
    max_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    status = StatusEnum.PENDING.value
    expires_at = LazyFunction(lambda: timezone.now() + timedelta(days=30))


class PurchaseHistoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating purchase history records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = PurchaseHistory

    buyer = SubFactory(BuyerFactory)
    dealership = SubFactory("dealers.factories.DealershipFactory")
    car_model = SubFactory(CarModelFactory)
    offer = SubFactory(OfferFactory)
    quantity = 1
    transaction = SubFactory(TransactionFactory)
    price_paid = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    cost_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


class SupplyHistoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating supply history records (dealership -> supplier)."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SupplyHistory

    dealership = SubFactory("dealers.factories.DealershipFactory")
    supplier = SubFactory("suppliers.factories.SupplierFactory")
    car_model = SubFactory(CarModelFactory)
    offer = SubFactory(OfferFactory)
    transaction = SubFactory(TransactionFactory)
    quantity = Faker("random_int", min=1, max=10)
    unit_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    total_price = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
