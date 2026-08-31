from core.otp_utils import generate_and_send_otp, verify_otp
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import Buyer
from accounts.permissions import IsOwnerProfile

from .forms import LoginForm, SignUpForm
from .serializers import (
    BuyerSerializer,
    BuyerUpdateSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
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


def signup_view(request: HttpRequest):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


def login_view(request: HttpRequest):
    form = LoginForm(data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(
                username=username,
                password=password,
            )

            if user is not None:
                generate_and_send_otp(user)
                request.session["pending_user_id"] = user.id  # pyright: ignore[reportAttributeAccessIssue]

                return redirect("verify_otp")
            else:
                return render(
                    request, "login.html", {"error": "Invalid login or password"}
                )

    return render(request, "login.html", {"form": form})


def verify_otp_view(request: HttpRequest):
    pending_user_id = request.session.get("pending_user_id")

    if not pending_user_id:
        return redirect("login")

    User = get_user_model()

    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        return redirect("login")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        is_valid, error_msg = verify_otp(user, entered_otp)

        if is_valid:
            del request.session["pending_user_id"]
            login(request, user)
            return redirect("home")

        else:
            return render(request, "verify_otp.html", {"error": error_msg})

    return render(request, "verify_otp.html")


def logout_view(request: HttpRequest):
    logout(request)

    return redirect("login")
