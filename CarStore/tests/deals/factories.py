"""
Factory Boy factories for the deals application.
"""

from datetime import timedelta

import factory
from core.enums import StatusEnum
from deals.models import (
    Offer,
    PurchaseHistory,
    Transaction,
)
from django.utils import timezone
from factory.declarations import LazyFunction, SubFactory
from factory.faker import Faker
from tests.accounts.factories import BuyerFactory
from tests.cars.factories import CarModelFactory


class OfferFactory(factory.django.DjangoModelFactory):
    """Factory for creating buyer offers."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Offer

    buyer = SubFactory(BuyerFactory)
    car_model = SubFactory(CarModelFactory)
    max_price = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    status = StatusEnum.PENDING.value
    expires_at = LazyFunction(lambda: timezone.now() + timedelta(days=30))


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for creating transactions."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Transaction

    transaction_type = Transaction.TransactionType.PURCHASE
    amount = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    buyer = SubFactory(BuyerFactory)
    # Requires dealers.factories.DealershipFactory
    dealership = SubFactory("dealers.factories.DealershipFactory")
    # Requires suppliers.factories.SupplierFactory
    supplier = SubFactory("suppliers.factories.SupplierFactory")
    car_model = SubFactory(CarModelFactory)
    offer = SubFactory(OfferFactory)
    reason = Faker("text", max_nb_chars=100)


class PurchaseHistoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating purchase history records."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = PurchaseHistory

    buyer = SubFactory(BuyerFactory)
    offer = SubFactory(OfferFactory)
    transaction = SubFactory(TransactionFactory)
    dealership = SubFactory("dealers.factories.DealershipFactory")
    car_model = SubFactory(CarModelFactory)
    price_paid = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
