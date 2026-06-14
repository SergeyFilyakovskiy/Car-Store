from core.models import BaseModel
from django.db import models


class SalesStatistics(BaseModel):
    """Aggregated sales statistics for reporting.

    Attributes:
        id: Unique statistics record identifier.
        dealership: Related dealership.
        total_sales: Total number of completed sales.
        total_revenue: Total revenue in USD.
        unique_buyers: Number of unique buyers.
        total_profit: Total profit in USD.
        calculated_at: Timestamp when the statistics were calculated.
    """

    dealership = models.OneToOneField(
        "dealers.Dealership",
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="Dealership",
    )
    total_sales = models.PositiveIntegerField(default=0, verbose_name="Total sales")
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Total revenue",
    )
    unique_buyers = models.PositiveIntegerField(default=0, verbose_name="Unique buyers")
    total_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Total profit",
    )
    calculated_at = models.DateTimeField(auto_now=True, verbose_name="Calculated at")

    class Meta:  # type: ignore
        verbose_name = "Sales statistics"
        verbose_name_plural = "Sales statistics"

    def __str__(self) -> str:
        return f"{self.dealership.name} statistics"
