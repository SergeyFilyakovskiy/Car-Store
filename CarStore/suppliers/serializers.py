from cars.models import CarModel
from rest_framework import serializers

from suppliers.models import (
    Supplier,
    SupplierCar,
    SupplierLoyaltyDiscount,
    SupplierPromo,
    SupplierPromoModel,
)


class SupplierSerializer(serializers.ModelSerializer):
    """Serialize supplier data."""

    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "country",
            "location",
            "founded_year",
            "description",
            "account_id",
        )
        read_only_fields = ("id", "account_id")


class SupplierCarSerializer(serializers.ModelSerializer):
    """Serialize supplier car offers."""

    supplier = serializers.StringRelatedField(source="supplier", read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        source="supplier",
        queryset=Supplier.objects.all(),
        write_only=True,
    )
    car_model = serializers.StringRelatedField(source="car_model", read_only=True)
    car_model_id = serializers.PrimaryKeyRelatedField(
        source="car_model",
        queryset=CarModel.objects.all(),
        write_only=True,
    )

    class Meta:
        model = SupplierCar
        fields = (
            "id",
            "supplier",
            "supplier_id",
            "car_model",
            "car_model_id",
            "base_price",
            "stock_quantity",
        )
        read_only_fields = ("id",)


class SupplierLoyaltyDiscountSerializer(serializers.ModelSerializer):
    """Serialize supplier loyalty discounts."""

    class Meta:
        model = SupplierLoyaltyDiscount
        fields = ("id", "supplier_id", "dealer_id", "discount_pct", "min_purchases")
        read_only_fields = ("id",)


class SupplierPromoSerializer(serializers.ModelSerializer):
    """Serialize supplier promotions."""

    supplier = serializers.StringRelatedField(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        source="supplier",
        queryset=Supplier.objects.all(),
        write_only=True,
    )

    class Meta:
        model = SupplierPromo
        fields = (
            "id",
            "supplier",
            "supplier_id",
            "name",
            "description",
            "discount_pct",
            "start_date",
            "end_date",
        )
        read_only_fields = ("id",)


class SupplierPromoModelSerializer(serializers.ModelSerializer):
    """Serialize relation between supplier promo and car model."""

    promo = serializers.StringRelatedField(read_only=True)
    promo_id = serializers.PrimaryKeyRelatedField(
        source="promo", queryset=SupplierPromo.objects.all(), write_only=True
    )
    car_model = serializers.StringRelatedField(read_only=True)
    car_model_id = serializers.PrimaryKeyRelatedField(
        source="car_model", queryset=CarModel.objects.all(), write_only=True
    )

    class Meta:
        model = SupplierPromoModel
        fields = ("id", "promo", "promo_id", "car_model", "car_model_id")
        read_only_fields = ("id",)
