from analytics.models import SalesStatistics
from rest_framework import serializers

from deals.models import Offer, PurchaseHistory, Transaction


class OfferSerializer(serializers.ModelSerializer):
    """Serialize buyer offers."""

    class Meta:
        model = Offer
        fields = ("id", "buyer", "car_model", "max_price", "status", "expires_at")
        read_only_fields = ("id", "status")


class TransactionSerializer(serializers.ModelSerializer):
    """Serialize transactions."""

    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_type",
            "amount",
            "buyer",
            "dealership",
            "supplier",
            "car_model",
            "offer",
            "reason",
        )
        read_only_fields = ("id",)


class PurchaseHistorySerializer(serializers.ModelSerializer):
    """Serialize purchase history records."""

    class Meta:
        model = PurchaseHistory
        fields = (
            "id",
            "buyer",
            "offer",
            "transaction",
            "dealership",
            "car_model",
            "price_paid",
            "purchased_at",
        )
        read_only_fields = ("id", "purchased_at")


class SalesStatisticsSerializer(serializers.ModelSerializer):
    """Serialize aggregated sales statistics."""

    class Meta:
        model = SalesStatistics
        fields = (
            "id",
            "dealership",
            "total_sales",
            "total_revenue",
            "unique_buyers",
            "total_profit",
            "calculated_at",
        )
        read_only_fields = ("id", "calculated_at")
