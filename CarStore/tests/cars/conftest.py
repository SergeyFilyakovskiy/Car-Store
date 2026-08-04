"""
Test fixtures for the 'cars' application.
"""

import pytest
from tests.cars.factories import CarBrandFactory, CarModelFactory


@pytest.fixture
def car_brand_factory():
    """Returns the CarBrandFactory."""
    return CarBrandFactory


@pytest.fixture
def car_model_factory():
    """Returns the CarModelFactory."""
    return CarModelFactory


@pytest.fixture
def car_brand(db):
    """Creates a test automotive brand."""
    return CarBrandFactory(name="Toyota", country="Japan")


@pytest.fixture
def car_model(db, car_brand):
    """Creates a test model of the car."""
    return CarModelFactory(
        brand=car_brand,
        name="Camry",
        body_type="sedan",
        fuel_type="petrol",
        transmission="AT",
        drive_type="FWD",
        engine_volume=2.5,
        horsepower=200,
        year_form=2020,
        year_to=2023,
    )


@pytest.fixture
def multiple_car_brands(db):
    """Creates several car brands for list testing."""
    return CarBrandFactory.create_batch(5)


@pytest.fixture
def multiple_car_models(db, car_brand):
    """Creates several car models for list testing."""
    return CarModelFactory.create_batch(5, brand=car_brand)
