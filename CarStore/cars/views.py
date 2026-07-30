from rest_framework import generics, permissions

from .models import CarBrand, CarModel
from .serializers import CarBrandSerializer, CarModelSerializer


class CarBrandListCreateAPIView(generics.ListCreateAPIView):
    """Get a list of brands or create a new one."""

    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CarBrandDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific brand."""

    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CarModelListCreateAPIView(generics.ListCreateAPIView):
    """Get a list of models or create a new one."""

    queryset = CarModel.objects.select_related("brand").all()
    serializer_class = CarModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Оптимизация: при создании не нужен select_related, только при чтении
        if self.request.method == "GET":
            return CarModel.objects.select_related("brand").all()
        return super().get_queryset()


class CarModelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific model."""

    queryset = CarModel.objects.select_related("brand").all()
    serializer_class = CarModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
