# views.py
from core.otp_utils import generate_and_send_otp, verify_otp
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import Buyer
from accounts.permissions import IsOwnerProfile

from .serializers import (
    BuyerSerializer,
    BuyerUpdateSerializer,
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterAPIView(generics.CreateAPIView):
    """Register a new user."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    """Obtain JWT pair with custom claims."""

    serializer_class = CustomTokenObtainPairSerializer


class BuyerProfileAPIView(generics.RetrieveAPIView):
    """Get the current buyer profile."""

    serializer_class = BuyerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return get_object_or_404(Buyer, user=self.request.user)


class BuyerProfileUpdateAPIView(generics.UpdateAPIView):
    """Update buyer profile fields."""

    serializer_class = BuyerUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return get_object_or_404(Buyer, user=self.request.user)


@extend_schema(
    tags=["accounts"],
    summary="Login with password (Step 1)",
    description="Verifies password, sends OTP, returns a temporary pending_token.",
    request=LoginSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "pending_token": {"type": "string"},
                "message": {"type": "string"},
            },
        }
    },
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def api_login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]  # type: ignore
    password = serializer.validated_data["password"]  # type: ignore

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    cooldown_key = f"otp_cooldown_{user.id}"  # pyright: ignore[reportAttributeAccessIssue]
    if cache.get(cooldown_key):
        return Response(
            {"error": "Too many requests. Please wait 60 seconds."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    generate_and_send_otp(user)

    cache.set(cooldown_key, True, timeout=60)

    pending_token = f"pending_{user.id}"  # pyright: ignore[reportAttributeAccessIssue]
    cache.set(pending_token, user.id, timeout=300)  # pyright: ignore[reportAttributeAccessIssue]

    return Response(
        {"message": "OTP sent to email", "pending_token": pending_token},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["accounts"],
    summary="Verify OTP (Step 2)",
    description="Verifies OTP and returns JWT tokens.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "otp": {"type": "string"},
                "pending_token": {"type": "string"},
            },
            "required": ["otp", "pending_token"],
        }
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "access": {"type": "string"},
                "refresh": {"type": "string"},
                "user": {"type": "object"},
            },
        }
    },
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def api_verify_otp_view(request):
    pending_token = request.data.get("pending_token")
    otp = request.data.get("otp")

    if not pending_token or not otp:
        return Response(
            {"error": "pending_token and otp are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_id = cache.get(pending_token)
    if not user_id:
        return Response(
            {"error": "Invalid or expired pending_token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

    is_valid, error_msg = verify_otp(user, otp)

    if is_valid:
        cache.delete(pending_token)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    return Response({"error": error_msg}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    tags=["accounts"],
    summary="Logout",
    description="Blacklists the refresh token (if using SimpleJWT blacklist app) or just returns success.",
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def api_logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
    except KeyError:
        return Response({"error": "Refresh token is required"}, status=400)

    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
