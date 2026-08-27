"""
Views for the suppliers application.

Provides CRUD endpoints for suppliers and their related entities
(cars, loyalty discounts, promotions).
"""

from accounts.permissions import IsSupplier
from rest_framework import generics, permissions, serializers

from suppliers.models import (
    Supplier,
    SupplierCar,
    SupplierLoyaltyDiscount,
    SupplierPromo,
    SupplierPromoModel,
)
from suppliers.serializers import (
    SupplierCarSerializer,
    SupplierLoyaltyDiscountSerializer,
    SupplierPromoModelSerializer,
    SupplierPromoSerializer,
    SupplierSerializer,
)


class IsSupplierOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a supplier to access or modify
    the supplier and its related objects. Prevents IDOR vulnerabilities.
    """

    def has_object_permission(self, request, view, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
        # 1. Supplier model (direct ownership)
        if hasattr(obj, "account_id") and obj.account_id is not None:
            return obj.account_id == request.user

        # 2. Models with 'supplier_id' (SupplierCar, SupplierLoyaltyDiscount)
        if hasattr(obj, "supplier_id") and obj.supplier_id is not None:
            return obj.supplier.account_id == request.user

        # 3. Models with 'supplier' (SupplierPromo)
        if hasattr(obj, "supplier") and obj.supplier is not None:
            return obj.supplier.account_id == request.user

        # 4. Models with 'promo' (SupplierPromoModel)
        if hasattr(obj, "promo") and obj.promo is not None:
            return obj.promo.supplier.account_id == request.user

        return False


# ==============================================================================
# Supplier Views
# ==============================================================================


class SupplierListCreateAPIView(generics.ListCreateAPIView):
    """List all suppliers or create a new one."""

    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplier]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Supplier.objects.all()

    def perform_create(self, serializer):
        serializer.save(account_id=self.request.user)


class SupplierDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific supplier."""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]


# ==============================================================================
# Supplier Car Views
# ==============================================================================


class SupplierCarListCreateAPIView(generics.ListCreateAPIView):
    """List or create car offers for the user's suppliers."""

    serializer_class = SupplierCarSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierCar.objects.filter(supplier__account_id=self.request.user)

    def perform_create(self, serializer):
        supplier= serializer.validated_data.get("supplier")
        if supplier.account_id != self.request.user:
            raise serializers.ValidationError(
                {"supplier_id": "You do not own this supplier."}
            )
        serializer.save()


class SupplierCarDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific supplier car offer."""

    serializer_class = SupplierCarSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierCar.objects.filter(supplier_id__account_id=self.request.user)


# ==============================================================================
# Supplier Loyalty Discount Views
# ==============================================================================


class SupplierLoyaltyDiscountListCreateAPIView(generics.ListCreateAPIView):
    """List or create loyalty discounts for the user's suppliers."""

    serializer_class = SupplierLoyaltyDiscountSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierLoyaltyDiscount.objects.filter(
            supplier__account_id=self.request.user
        )

    def perform_create(self, serializer):
        supplier_id = serializer.validated_data.get("supplier_id")
        if supplier_id.account_id != self.request.user:
            raise serializers.ValidationError(
                {"supplier_id": "You do not own this supplier."}
            )
        serializer.save()


class SupplierLoyaltyDiscountDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific loyalty discount."""

    serializer_class = SupplierLoyaltyDiscountSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierLoyaltyDiscount.objects.filter(
            supplier__account_id=self.request.user
        )


# ==============================================================================
# Supplier Promo Views
# ==============================================================================


class SupplierPromoListCreateAPIView(generics.ListCreateAPIView):
    """List or create promotions for the user's suppliers."""

    serializer_class = SupplierPromoSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierPromo.objects.filter(supplier__account_id=self.request.user)

    def perform_create(self, serializer):
        supplier = serializer.validated_data.get("supplier")
        if supplier.account_id != self.request.user:
            raise serializers.ValidationError(
                {"supplier": "You do not own this supplier."}
            )
        serializer.save()


class SupplierPromoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific supplier promotion."""

    serializer_class = SupplierPromoSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierPromo.objects.filter(supplier__account_id=self.request.user)


# ==============================================================================
# Supplier Promo Model Views
# ==============================================================================


class SupplierPromoModelListCreateAPIView(generics.ListCreateAPIView):
    """List or create links between supplier promotions and car models."""

    serializer_class = SupplierPromoModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierPromoModel.objects.filter(
            promo__supplier__account_id=self.request.user
        )

    def perform_create(self, serializer):
        promo = serializer.validated_data.get("promo")
        if promo.supplier.account_id != self.request.user:
            raise serializers.ValidationError(
                {"promo": "You do not own this supplier's promotion."}
            )
        serializer.save()


class SupplierPromoModelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific promo-model link."""

    serializer_class = SupplierPromoModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplierOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return SupplierPromoModel.objects.filter(
            promo__supplier__account_id=self.request.user
        )
