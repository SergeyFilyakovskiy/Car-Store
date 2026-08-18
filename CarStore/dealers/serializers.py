"""
Serializers for the dealers application.
"""

from rest_framework import serializers

from dealers.models import (
    Dealership,
    DealershipInventory,
    DealershipPreference,
    DealershipPromo,
    DealershipPromoModel,
    DealershipSale,
    DealershipSupplier,
)


class DealershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealership
        fields = "__all__"
        read_only_fields = ("id", "account_id")


class DealershipInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipInventory
        fields = "__all__"
        read_only_fields = ("id",)


class DealershipPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipPreference
        fields = "__all__"
        read_only_fields = ("id",)


class DealershipPromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipPromo
        fields = "__all__"
        read_only_fields = ("id",)


class DealershipPromoModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipPromoModel
        fields = "__all__"
        read_only_fields = ("id",)


class DealershipSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipSale
        fields = "__all__"
        read_only_fields = ("id", "sold_at")


class DealershipSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealershipSupplier
        fields = "__all__"
        read_only_fields = ("id",)
