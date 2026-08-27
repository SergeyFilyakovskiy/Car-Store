"""
Factory Boy factories for the analytics application.
"""

import factory
from analytics.models import SalesStatistics
from django.utils import timezone
from factory.declarations import LazyFunction, SubFactory
from factory.faker import Faker


class SalesStatisticsFactory(factory.django.DjangoModelFactory):
    """Factory for creating sales statistics."""

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = SalesStatistics

    dealership = SubFactory("dealers.factories.DealershipFactory")
    total_sales = Faker("random_int", min=0, max=1000)
    total_revenue = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    unique_buyers = Faker("random_int", min=0, max=500)
    total_profit = Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    calculated_at = LazyFunction(timezone.now)
