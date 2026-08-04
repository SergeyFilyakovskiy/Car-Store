from django.urls import path

from . import views

urlpatterns = [
    path("brands/", views.CarBrandListCreateAPIView.as_view(), name="car-brand-list"),
    path(
        "brands/<uuid:pk>/",
        views.CarBrandDetailAPIView.as_view(),
        name="car-brand-detail",
    ),
    path("models/", views.CarModelListCreateAPIView.as_view(), name="car-model-list"),
    path(
        "models/<uuid:pk>/",
        views.CarModelDetailAPIView.as_view(),
        name="car-model-detail",
    ),
]
