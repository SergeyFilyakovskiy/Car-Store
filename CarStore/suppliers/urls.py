"""
URL configuration for the suppliers application.
"""

from django.urls import path

from . import views

app_name = "suppliers"

urlpatterns = [
    # Supplier
    path("", views.SupplierListCreateAPIView.as_view(), name="supplier-list-create"),
    path("<uuid:pk>/", views.SupplierDetailAPIView.as_view(), name="supplier-detail"),
    # Supplier Car
    path(
        "cars/",
        views.SupplierCarListCreateAPIView.as_view(),
        name="supplier-car-list-create",
    ),
    path(
        "cars/<uuid:pk>/",
        views.SupplierCarDetailAPIView.as_view(),
        name="supplier-car-detail",
    ),
    # Supplier Loyalty Discount
    path(
        "loyalty-discounts/",
        views.SupplierLoyaltyDiscountListCreateAPIView.as_view(),
        name="loyalty-discount-list-create",
    ),
    path(
        "loyalty-discounts/<uuid:pk>/",
        views.SupplierLoyaltyDiscountDetailAPIView.as_view(),
        name="loyalty-discount-detail",
    ),
    # Supplier Promo
    path(
        "promos/",
        views.SupplierPromoListCreateAPIView.as_view(),
        name="supplier-promo-list-create",
    ),
    path(
        "promos/<uuid:pk>/",
        views.SupplierPromoDetailAPIView.as_view(),
        name="supplier-promo-detail",
    ),
    # Supplier Promo Model
    path(
        "promo-models/",
        views.SupplierPromoModelListCreateAPIView.as_view(),
        name="supplier-promo-model-list-create",
    ),
    path(
        "promo-models/<uuid:pk>/",
        views.SupplierPromoModelDetailAPIView.as_view(),
        name="supplier-promo-model-detail",
    ),
]
