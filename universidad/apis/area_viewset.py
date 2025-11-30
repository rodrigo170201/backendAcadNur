# universidad/views/area_viewset.py
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, AllowAny, SAFE_METHODS
from universidad.models import Area

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'


class CustomPermission(DjangoModelPermissions):
    """Permite lectura pública (GET), pero protege escritura."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # Permitir GET, HEAD, OPTIONS sin login
        return super().has_permission(request, view)


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [CustomPermission]
