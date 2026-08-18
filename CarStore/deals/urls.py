"""
URL configuration for the deals application.
"""

from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    # Offers
    path("offers/", views.OfferListCreateAPIView.as_view(), name="offer-list-create"),
    path(
        "offers/<uuid:pk>/",
        views.OfferDetailAPIView.as_view(),
        name="offer-detail",
    ),
    # Transactions
    path(
        "transactions/",
        views.TransactionListAPIView.as_view(),
        name="transaction-list",
    ),
    path(
        "transactions/<uuid:pk>/",
        views.TransactionDetailAPIView.as_view(),
        name="transaction-detail",
    ),
    # Purchase History
    path(
        "purchase-history/",
        views.PurchaseHistoryListAPIView.as_view(),
        name="purchase-history-list",
    ),
    path(
        "purchase-history/<uuid:pk>/",
        views.PurchaseHistoryDetailAPIView.as_view(),
        name="purchase-history-detail",
    ),
]
