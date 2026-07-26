from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import Buyer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Public user representation
    """

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")


class RegisterSerializer(serializers.ModelSerializer):
    """Register a new user"""

    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "role", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Validate login credentials for API login."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Return JWT tokens with custom user claims."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data  # type: ignore
        return data


class BuyerSerializer(serializers.ModelSerializer):
    """Serialize buyer prolife data."""

    user = UserSerializer(source="user_id", read_only=True)

    class Meta:
        model = Buyer
        fields = (
            "id",
            "user",
            "balance",
            "date_of_birth",
            "gender",
            "phone",
            "country",
            "location",
            "preferred_body_type",
            "preferred_fuel_type",
        )


class BuyerUpdateSerializer(serializers.ModelSerializer):
    """Update buyer profile data."""

    class Meta:
        model = Buyer
        fields = (
            "balance",
            "date_of_birth",
            "gender",
            "phone",
            "country",
            "location",
            "preferred_body_type",
            "preferred_fuel_type",
        )
