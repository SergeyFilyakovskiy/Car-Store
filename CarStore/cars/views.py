from rest_framework import generics, permissions

from .models import CarBrand, CarModel
from .serializers import CarBrandSerializer, CarModelSerializer


class CarBrandListCreateAPIView(generics.ListCreateAPIView):
    """Получить список брендов или создать новый."""

    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CarBrandDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Получить, обновить или удалить конкретный бренд."""

    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CarModelListCreateAPIView(generics.ListCreateAPIView):
    """Получить список моделей или создать новую."""

    queryset = CarModel.objects.select_related("brand").all()
    serializer_class = CarModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Оптимизация: при создании не нужен select_related, только при чтении
        if self.request.method == "GET":
            return CarModel.objects.select_related("brand").all()
        return super().get_queryset()


class CarModelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Получить, обновить или удалить конкретную модель."""

    queryset = CarModel.objects.select_related("brand").all()
    serializer_class = CarModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
