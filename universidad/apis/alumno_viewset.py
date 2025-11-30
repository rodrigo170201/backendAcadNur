from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from universidad.models import Alumno


# --- SERIALIZER ---
class AlumnoSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    photo_profile = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Alumno
        fields = [
            'id',
            'nombre_completo',
            'email',
            'email_secundario',
            'password',
            'photo_profile',
            'numero_registro',
            'fecha_creacion',
            'rol'
        ]
        read_only_fields = ['id', 'numero_registro', 'fecha_creacion', 'rol']
        extra_kwargs = {'password': {'write_only': True}}

    def get_rol(self, obj):
        if obj.groups.exists():
            return obj.groups.first().name
        return "Alumno"

    def create(self, validated_data):
        # Encriptar la contraseña antes de guardar
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Permite que el alumno actualice su propio perfil.
        """
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.password = make_password(password)

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
class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    lookup_field = 'numero_registro'
    lookup_value_regex = r'\d+'

    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get_permissions(self):
        """
        Permite que:
        - 'create' sea público (registro)
        - 'mi_perfil' y 'actualizar_mi_perfil' accesibles al alumno autenticado
        - el resto solo para admins
        """
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['mi_perfil', 'actualizar_mi_perfil']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        password = serializer.validated_data.get('password')
        if password:
            serializer.validated_data['password'] = make_password(password)
        serializer.save()

    # 🔹 Endpoint: ver perfil del alumno autenticado
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mi_perfil(self, request):
        alumno = request.user
        serializer = self.get_serializer(alumno)
        return Response(serializer.data)

    # 🔹 Endpoint: actualizar perfil del alumno autenticado
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def actualizar_mi_perfil(self, request):
        alumno = request.user
        serializer = self.get_serializer(alumno, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "mensaje": "Perfil actualizado correctamente",
            "data": serializer.data
        })
