"""
Views for the dealers application.

Provides CRUD endpoints for dealerships and their related entities
(inventory, preferences, suppliers, promotions, and sales).
"""

from accounts.permissions import IsDealership
from rest_framework import generics, permissions, serializers

from dealers.models import (
    Dealership,
    DealershipInventory,
    DealershipPreference,
    DealershipPromo,
    DealershipPromoModel,
    DealershipSale,
    DealershipSupplier,
)
from dealers.serializers import (
    DealershipInventorySerializer,
    DealershipPreferenceSerializer,
    DealershipPromoModelSerializer,
    DealershipPromoSerializer,
    DealershipSaleSerializer,
    DealershipSerializer,
    DealershipSupplierSerializer,
)


class IsDealershipOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a dealership to access or modify
    the dealership and its related objects. Prevents IDOR vulnerabilities.
    """

    def has_object_permission(self, request, view, obj):  # pyright: ignore[reportIncompatibleMethodOverride]

        if hasattr(obj, "account_id") and obj.account_id is not None:
            return obj.account_id == request.user

        if hasattr(obj, "dealership") and obj.dealership is not None:
            return obj.dealership.account_id == request.user

        if hasattr(obj, "dealer_id") and obj.dealer_id is not None:
            return obj.dealer_id.account_id == request.user

        if hasattr(obj, "dealer") and obj.dealer is not None:
            return obj.dealer.account_id == request.user

        if hasattr(obj, "promo") and obj.promo is not None:
            return obj.promo.dealer.account_id == request.user

        return False


# ==============================================================================
# Dealership Views
# ==============================================================================


class DealershipListCreateAPIView(generics.ListCreateAPIView):
    """List all dealerships or create a new one."""

    serializer_class = DealershipSerializer


    permission_classes = [permissions.IsAuthenticated, IsDealership]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Dealership.objects.all()

    def perform_create(self, serializer):

        serializer.save(account_id=self.request.user)


class DealershipDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific dealership."""

    queryset = Dealership.objects.all()
    serializer_class = DealershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]


# ==============================================================================
# Dealership Preference Views
# ==============================================================================


class DealershipPreferenceListCreateAPIView(generics.ListCreateAPIView):
    """List or create preferences for the user's dealerships."""

    serializer_class = DealershipPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPreference.objects.filter(
            dealer_id__account_id=self.request.user
        )

    def perform_create(self, serializer):
        dealer_id = serializer.validated_data.get("dealer_id")
        if dealer_id.account_id != self.request.user:
            raise serializers.ValidationError(
                {"dealer_id": "You do not own this dealership."}
            )
        serializer.save()


class DealershipPreferenceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific dealership preference."""

    serializer_class = DealershipPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPreference.objects.filter(
            dealer_id__account_id=self.request.user
        )


# ==============================================================================
# Dealership Inventory Views
# ==============================================================================


class DealershipInventoryListCreateAPIView(generics.ListCreateAPIView):
    """List or create inventory items for the user's dealerships."""

    serializer_class = DealershipInventorySerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipInventory.objects.filter(
            dealer_id__account_id=self.request.user
        )

    def perform_create(self, serializer):
        dealer_id = serializer.validated_data.get("dealer_id")
        if dealer_id.account_id != self.request.user:
            raise serializers.ValidationError(
                {"dealer_id": "You do not own this dealership."}
            )
        serializer.save()


class DealershipInventoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific inventory item."""

    serializer_class = DealershipInventorySerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipInventory.objects.filter(
            dealer_id__account_id=self.request.user
        )


# ==============================================================================
# Dealership Supplier Views
# ==============================================================================


class DealershipSupplierListCreateAPIView(generics.ListCreateAPIView):
    """List or create best supplier links for the user's dealerships."""

    serializer_class = DealershipSupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipSupplier.objects.filter(
            dealer_id__account_id=self.request.user
        )

    def perform_create(self, serializer):
        dealer_id = serializer.validated_data.get("dealer_id")
        if dealer_id.account_id != self.request.user:
            raise serializers.ValidationError(
                {"dealer_id": "You do not own this dealership."}
            )
        serializer.save()


class DealershipSupplierDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific supplier link."""

    serializer_class = DealershipSupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipSupplier.objects.filter(
            dealer_id__account_id=self.request.user
        )


# ==============================================================================
# Dealership Promo Views
# ==============================================================================


class DealershipPromoListCreateAPIView(generics.ListCreateAPIView):
    """List or create promotions for the user's dealerships."""

    serializer_class = DealershipPromoSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPromo.objects.filter(dealer__account_id=self.request.user)

    def perform_create(self, serializer):
        dealer = serializer.validated_data.get("dealer")
        if dealer.account_id != self.request.user:
            raise serializers.ValidationError(
                {"dealer": "You do not own this dealership."}
            )
        serializer.save()


class DealershipPromoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific promotion."""

    serializer_class = DealershipPromoSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPromo.objects.filter(dealer__account_id=self.request.user)


# ==============================================================================
# Dealership Promo Model Views
# ==============================================================================


class DealershipPromoModelListCreateAPIView(generics.ListCreateAPIView):
    """List or create links between promotions and car models."""

    serializer_class = DealershipPromoModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPromoModel.objects.filter(
            promo__dealer__account_id=self.request.user
        )

    def perform_create(self, serializer):
        promo = serializer.validated_data.get("promo")
        if promo.dealer.account_id != self.request.user:
            raise serializers.ValidationError(
                {"promo": "You do not own this dealership's promotion."}
            )
        serializer.save()


class DealershipPromoModelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific promo-model link."""

    serializer_class = DealershipPromoModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipPromoModel.objects.filter(
            promo__dealer__account_id=self.request.user
        )


# ==============================================================================
# Dealership Sale Views (Read-Only)
# ==============================================================================


class DealershipSaleListAPIView(generics.ListAPIView):
    """List completed sales for the user's dealerships."""

    serializer_class = DealershipSaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipSale.objects.filter(dealership__account_id=self.request.user)


class DealershipSaleDetailAPIView(generics.RetrieveAPIView):
    """Retrieve details of a specific completed sale."""

    serializer_class = DealershipSaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealershipOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return DealershipSale.objects.filter(dealership__account_id=self.request.user)
