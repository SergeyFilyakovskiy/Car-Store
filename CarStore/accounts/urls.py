from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .payment_webhook import payment_webhook
from .views import (
    BuyerProfileAPIView,
    BuyerProfileUpdateAPIView,
    CreateTopUpView,
    CustomTokenObtainPairView,
    RegisterAPIView,
    TopUpCancelView,
    TopUpStatusView,
    api_login_view,
    api_verify_otp_view,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("buyer/profile/", BuyerProfileAPIView.as_view(), name="buyer-profile"),
    path(
        "buyer/profile/update/",
        BuyerProfileUpdateAPIView.as_view(),
        name="buyer-profile-update",
    ),
    path("login/", api_login_view, name="login"),
    path("verify-otp/", api_verify_otp_view, name="verify_otp"),
    path("topup/", CreateTopUpView.as_view(), name="create-topup"),
    path("topup/<int:id>/", TopUpStatusView.as_view(), name="topup-status"),
    path("topup/<int:id>/cancel/", TopUpCancelView.as_view(), name="topup-cancel"),
    path("webhooks/payment/", payment_webhook, name="payment-webhook"),
]
