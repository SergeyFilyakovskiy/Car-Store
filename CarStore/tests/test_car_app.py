from typing import cast

import pytest
from cars.models import CarBrand
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.fast
def test_create_car_brand():
    client = APIClient()
    from accounts.models import User

    user = User.objects.create_user(
        username="admin", password="StrongPass123!", email="a@b.com"
    )
    client.force_authenticate(user=user)

    response = cast(
        Response,
        client.post(
            reverse("car-brand-list"),
            {"name": "Toyota", "country": "Japan"},
            format="json",
        ),
    )
    assert response.status_code == 201
    assert CarBrand.objects.filter(name="Toyota").exists()
