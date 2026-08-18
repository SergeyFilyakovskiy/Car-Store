from rest_framework import serializers

from suppliers.models import (
    Supplier,
    SupplierCar,
    SupplierLoyaltyDiscount,
    SupplierPromo,
    SupplierPromoModel,
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ("id", "account_id")


class SupplierCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierCar
        fields = "__all__"
        read_only_fields = ("id",)


class SupplierLoyaltyDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierLoyaltyDiscount
        fields = "__all__"
        read_only_fields = ("id",)


class SupplierPromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPromo
        fields = "__all__"
        read_only_fields = ("id",)


class SupplierPromoModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPromoModel
        fields = "__all__"
        read_only_fields = ("id",)
