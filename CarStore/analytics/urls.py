"""
URL configuration for the analytics application.
"""

from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path(
        "",
        views.SalesStatisticsListAPIView.as_view(),
        name="sales-statistics-list",
    ),
    path(
        "<uuid:pk>/",
        views.SalesStatisticsDetailAPIView.as_view(),
        name="sales-statistics-detail",
    ),
]
