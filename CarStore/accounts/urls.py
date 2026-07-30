from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    BuyerProfileAPIView,
    BuyerProfileUpdateAPIView,
    CustomTokenObtainPairView,
    RegisterAPIView,
    login_view,
    signup_view,
)

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token-obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("buyer/profile/", BuyerProfileAPIView.as_view(), name="buyer-profile"),
    path(
        "buyer/profile/update/",
        BuyerProfileUpdateAPIView.as_view(),
        name="buyer-profile-update",
    ),
]
