from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    BuyerProfileAPIView,
    BuyerProfileUpdateAPIView,
    CustomTokenObtainPairView,
    RegisterAPIView,
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
]
