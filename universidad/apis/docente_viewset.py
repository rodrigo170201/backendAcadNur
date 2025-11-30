from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from universidad.models import Docente
from django.contrib.auth import get_user_model

User = get_user_model()


# --- SERIALIZER ---
class DocenteSerializer(serializers.ModelSerializer):
    # Campos del usuario relacionados
    nombre_completo = serializers.CharField(source='user.nombre_completo', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    email_secundario = serializers.EmailField(source='user.email_secundario', read_only=True)
    photo_profile = serializers.ImageField(source='user.photo_profile', required=False, allow_null=True)
    rol = serializers.SerializerMethodField()

    class Meta:
        model = Docente
        fields = [
            'id',
            'nombre_completo',
            'email',
            'email_secundario',
            'photo_profile',
            'descripcion',
            'numero_registro',
            'fecha_registro',
            'rol'
        ]
        read_only_fields = ['id', 'numero_registro', 'fecha_registro', 'rol']

    def get_rol(self, obj):
        if obj.user.groups.exists():
            return obj.user.groups.first().name
        return "Docente"

    def update(self, instance, validated_data):
        """
        Actualiza también los datos del usuario asociado (solo el suyo).
        """
        user_data = validated_data.pop('user', {})

        # Actualizamos campos del modelo User (solo los permitidos)
        if 'photo_profile' in user_data:
            instance.user.photo_profile = user_data['photo_profile']

        # Si se actualiza la descripción (del modelo Docente)
        if 'descripcion' in validated_data:
            instance.descripcion = validated_data['descripcion']

        instance.user.save()
        instance.save()
        return instance


# --- PERMISO PERSONALIZADO ---
class IsAdminOnly(BasePermission):
    """
    Solo permite acceso a usuarios del grupo 'Administrador' o superusuarios.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.groups.filter(name='Administrador').exists()
                or request.user.is_superuser
            )
        )


# --- VIEWSET ---
class DocenteViewSet(viewsets.ModelViewSet):
    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer
    lookup_field = 'numero_registro'
    lookup_value_regex = r'\d+'
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get_permissions(self):
        """
        Bloquea el método POST ya que el registro se hace desde UserViewSet.
        """
        if self.action == 'create':
            raise PermissionDenied("El registro de docentes solo puede hacerse desde 'user_viewset.py'.")
        # El endpoint 'mi_perfil' no necesita ser admin
        if self.action in ['mi_perfil', 'actualizar_mi_perfil']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        """
        Al eliminar un docente, también se elimina el usuario asociado.
        """
        instance.user.delete()
        instance.delete()

    # 🔹 Endpoint para ver los datos del docente logueado
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mi_perfil(self, request):
        try:
            docente = request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")
        serializer = self.get_serializer(docente)
        return Response(serializer.data)

    # 🔹 Endpoint para actualizar SOLO el perfil del docente logueado
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def actualizar_mi_perfil(self, request):
        try:
            docente = request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")

        serializer = self.get_serializer(docente, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "mensaje": "Perfil actualizado correctamente",
            "data": serializer.data
        })
