from rest_framework import serializers

from cars.models import CarBrand, CarModel


class CarBrandSerializer(serializers.ModelSerializer):
    """Serialize car brand data."""

    class Meta:
        model = CarBrand
        fields = ("id", "name", "country")
        read_only_fields = ("id",)


class CarModelSerializer(serializers.ModelSerializer):
    """Serialize car model data."""

    brand = CarBrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        source="brand",
        queryset=CarBrand.objects.all(),
        write_only=True,
    )

    class Meta:
        model = CarModel
        fields = (
            "id",
            "brand",
            "brand_id",
            "name",
            "body_type",
            "fuel_type",
            "transmission",
            "drive_type",
            "engine_volume",
            "horsepower",
            "year_form",
            "year_to",
        )
        read_only_fields = ("id",)
