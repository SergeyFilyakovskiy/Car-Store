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
    """Serialize dealership data."""

    class Meta:
        model = Dealership
        fields = ("id", "name", "country", "address", "balance", "account_id")
        read_only_fields = ("id",)


class DealershipPreferenceSerializer(serializers.ModelSerializer):
    """Serialize dealership car preferences."""

    class Meta:
        model = DealershipPreference
        fields = (
            "id",
            "dealer_id",
            "body_type",
            "fuel_type",
            "transmission",
            "drive_type",
            "min_hp",
            "max_hp",
            "min_price",
            "max_price",
        )
        read_only_fields = ("id",)


class DealershipInventorySerializer(serializers.ModelSerializer):
    """Serialize dealership inventory rows."""

    class Meta:
        model = DealershipInventory
        fields = ("id", "dealer_id", "car_model_id", "quantity", "sale_price")
        read_only_fields = ("id",)


class DealershipSupplierSerializer(serializers.ModelSerializer):
    """Serialize best supplier links for dealerships."""

    class Meta:
        model = DealershipSupplier
        fields = ("id", "dealer_id", "supplier_id", "car_model_id", "best_price")
        read_only_fields = ("id",)


class DealershipPromoSerializer(serializers.ModelSerializer):
    """Serialize dealership promotions."""

    class Meta:
        model = DealershipPromo
        fields = (
            "id",
            "dealer",
            "name",
            "description",
            "discount_pct",
            "start_date",
            "end_date",
        )
        read_only_fields = ("id",)


class DealershipPromoModelSerializer(serializers.ModelSerializer):
    """Serialize dealership promo to car model relations."""

    class Meta:
        model = DealershipPromoModel
        fields = ("id", "promo", "car_model")
        read_only_fields = ("id",)


class DealershipSaleSerializer(serializers.ModelSerializer):
    """Serialize dealership sales."""

    class Meta:
        model = DealershipSale
        fields = (
            "id",
            "dealership",
            "buyer",
            "car_model",
            "offer",
            "promo",
            "sale_price",
            "discount_applied",
            "sold_at",
        )
        read_only_fields = ("id", "sold_at")
