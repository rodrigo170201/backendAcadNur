from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from universidad.models import Leccion

class LeccionSerializer(serializers.ModelSerializer):
    seccion_nombre = serializers.CharField(source='seccion.nombre', read_only=True)
    material = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Leccion
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.material:
            try:
                if str(instance.material).lower().endswith(".pdf"):
                    ret['material'] = instance.material.build_url(resource_type="raw")
                else:
                    ret['material'] = instance.material.url
            except Exception:
                ret['material'] = None
        return ret

class LeccionViewSet(viewsets.ModelViewSet):
    queryset = Leccion.objects.all()
    serializer_class = LeccionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
