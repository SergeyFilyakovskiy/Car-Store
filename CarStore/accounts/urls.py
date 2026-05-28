from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import CustomTokenObtainPairView
from .views import login_view, signup_view

urlpatterns = [
    path("/signup", signup_view, name="signup"),
    path("/login", login_view, name="login"),
    path("/token", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "/token/refresh",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
