"""
Views for the analytics application.

Provides read-only endpoints for sales statistics.
Statistics are calculated automatically via Celery tasks.
"""

from accounts.permissions import IsDealership
from rest_framework import generics, permissions

from analytics.models import SalesStatistics
from analytics.serializers import SalesStatisticsSerializer


class IsStatisticsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a dealership to view its statistics.
    """

    def has_object_permission(self, request, view, obj):
        return obj.dealership.account_id == request.user


class SalesStatisticsListAPIView(generics.ListAPIView):
    """
    List sales statistics for the user's dealership.
    Only dealership owners can access this endpoint.
    """

    serializer_class = SalesStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealership]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SalesStatistics.objects.filter(dealership__account_id=self.request.user)


class SalesStatisticsDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve detailed sales statistics for a specific dealership.
    Only the dealership owner can access this endpoint.
    """

    serializer_class = SalesStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsStatisticsOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SalesStatistics.objects.filter(dealership__account_id=self.request.user)
