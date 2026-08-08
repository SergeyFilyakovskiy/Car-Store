"""
URL configuration for the dealers application.

Maps URL patterns to the corresponding view classes for dealership management,
inventory, preferences, suppliers, promotions, and sales.
"""

from django.urls import path

from . import views

app_name = "dealers"

urlpatterns = [
    # ========================================================================
    # Dealership Endpoints
    # ========================================================================
    path(
        "", views.DealershipListCreateAPIView.as_view(), name="dealership-list-create"
    ),
    path(
        "<uuid:pk>/", views.DealershipDetailAPIView.as_view(), name="dealership-detail"
    ),
    # ========================================================================
    # Dealership Preference Endpoints
    # ========================================================================
    path(
        "preferences/",
        views.DealershipPreferenceListCreateAPIView.as_view(),
        name="preference-list-create",
    ),
    path(
        "preferences/<uuid:pk>/",
        views.DealershipPreferenceDetailAPIView.as_view(),
        name="preference-detail",
    ),
    # ========================================================================
    # Dealership Inventory Endpoints
    # ========================================================================
    path(
        "inventory/",
        views.DealershipInventoryListCreateAPIView.as_view(),
        name="inventory-list-create",
    ),
    path(
        "inventory/<uuid:pk>/",
        views.DealershipInventoryDetailAPIView.as_view(),
        name="inventory-detail",
    ),
    # ========================================================================
    # Dealership Supplier Endpoints
    # ========================================================================
    path(
        "suppliers/",
        views.DealershipSupplierListCreateAPIView.as_view(),
        name="supplier-list-create",
    ),
    path(
        "suppliers/<uuid:pk>/",
        views.DealershipSupplierDetailAPIView.as_view(),
        name="supplier-detail",
    ),
    # ========================================================================
    # Dealership Promo Endpoints
    # ========================================================================
    path(
        "promos/",
        views.DealershipPromoListCreateAPIView.as_view(),
        name="promo-list-create",
    ),
    path(
        "promos/<uuid:pk>/",
        views.DealershipPromoDetailAPIView.as_view(),
        name="promo-detail",
    ),
    # ========================================================================
    # Dealership Promo Model Endpoints
    # ========================================================================
    path(
        "promo-models/",
        views.DealershipPromoModelListCreateAPIView.as_view(),
        name="promo-model-list-create",
    ),
    path(
        "promo-models/<uuid:pk>/",
        views.DealershipPromoModelDetailAPIView.as_view(),
        name="promo-model-detail",
    ),
    # ========================================================================
    # Dealership Sale Endpoints (Read-only)
    # ========================================================================
    path("sales/", views.DealershipSaleListAPIView.as_view(), name="sale-list"),
    path(
        "sales/<uuid:pk>/",
        views.DealershipSaleDetailAPIView.as_view(),
        name="sale-detail",
    ),
]
