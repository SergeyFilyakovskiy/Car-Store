from rest_framework import serializers

from analytics.models import SalesStatistics


class SalesStatisticsSerializer(serializers.ModelSerializer):
    """Serialize aggregated sales statistics."""

    dealership_name = serializers.CharField(source="dealership.name", read_only=True)

    class Meta:
        model = SalesStatistics
        fields = (
            "id",
            "dealership",
            "dealership_name",
            "total_sales",
            "total_revenue",
            "unique_buyers",
            "total_profit",
            "calculated_at",
        )
        read_only_fields = ("id", "calculated_at")
