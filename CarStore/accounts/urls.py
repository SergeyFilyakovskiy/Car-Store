from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import login_view, signup_view

urlpatterns = [
    path("/signup", signup_view, name="signup"),
    path("/login", login_view, name="login"),
    path("/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "/token/refresh",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
