from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from universidad.models import Leccion

class LeccionSerializer(serializers.ModelSerializer):
    seccion_nombre = serializers.CharField(source='seccion.nombre', read_only=True)

    class Meta:
        model = Leccion
        fields = '__all__'

class LeccionViewSet(viewsets.ModelViewSet):
    queryset = Leccion.objects.all()
    serializer_class = LeccionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
