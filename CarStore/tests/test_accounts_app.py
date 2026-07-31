from typing import cast

import pytest
from accounts.models import Buyer, User
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.fast
def test_register_api_success():
    client = APIClient()
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "password2": "testpassword",
        "role": "buyer",
    }
    response = cast(Response, client.post(reverse("register"), payload, format="json"))
    assert response.status_code == 201
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
@pytest.mark.fast
def test_buyer_profile_requires_auth():
    client = APIClient()
    response = cast(Response, client.get(reverse("buyer-profile")))
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.fast
def test_buyer_profile_with_auth():
    client = APIClient()
    user = User.objects.create_user(
        username="buyer1", password="testpassword", email="test@example.com"
    )
    Buyer.objects.create(
        user=user,
        balance=100.00,
        date_of_birth="2000-01-01",
        gender="M",
        phone="123",
        country="US",
        location="POINT(0 0)",
        preferred_body_type="SEDAN",
        preferred_fuel_type="PETROL",
    )

    client.force_authenticate(user=user)
    response = cast(Response, client.get(reverse("buyer-profile")))
    assert response.status_code == 200
    assert response.data["balance"] == "100.00"
