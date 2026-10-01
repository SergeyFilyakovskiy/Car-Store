
import factory
from accounts.models import (
    BalanceTopUp,
    Buyer,
    Entry,
    Transaction,
    User,
)
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

    username = Sequence(lambda n: f"user_{n}")
    email = LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = PostGenerationMethodCall("set_password", "StrongPass123!")
    role = "buyer"
    is_active = True
    is_verifyed = True  # по умолчанию email подтверждён
    balance = 0


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


class DealershipUserFactory(UserFactory):

    role = "dealership"


class SupplierUserFactory(UserFactory):

    role = "supplier"


class AdminUserFactory(UserFactory):

    role = "admin"


class TransactionFactory(factory.django.DjangoModelFactory):

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Transaction

    status = Transaction.Status.PENDING
    idempotency_key = Sequence(lambda n: f"tx-{n}")
    description = Faker("sentence")


class CompletedTransactionFactory(TransactionFactory):

    status = Transaction.Status.COMPLETED


class EntryFactory(factory.django.DjangoModelFactory):

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Entry

    transaction = SubFactory(TransactionFactory)
    user = SubFactory(UserFactory)
    amount = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    type = Entry.EntryType.CREDIT
    balance_after = None


class BalanceTopUpFactory(factory.django.DjangoModelFactory):

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = BalanceTopUp

    user = SubFactory(UserFactory)
    amount = Faker("pydecimal", left_digits=4, right_digits=2, min_value=10, max_value=1000, positive=True)
    payment_method = BalanceTopUp.PaymentMethod.CARD
    status = BalanceTopUp.Status.PENDING
