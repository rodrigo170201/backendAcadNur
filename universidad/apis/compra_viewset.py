from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, BasePermission
from rest_framework.response import Response

from universidad.apis.curso_viewset import CursoDetailFullSerializer
from universidad.models import Compra, Curso

# Importamos el serializer completo del curso
# ------------------- SERIALIZER DE CURSO (para lista de compras) -------------------
class CursoResumenSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    docente_nombre = serializers.CharField(source='docente.nombre_completo', read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio',
            'certificable',
            'modo_prueba',
            'photo_profile',
            'area_nombre',
            'docente_nombre'
        ]


# ------------------- SERIALIZER -------------------
class CompraSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.nombre_completo', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    curso_detalle = CursoResumenSerializer(source='curso', read_only=True)
    class Meta:
        model = Compra
        fields = '__all__'


# ------------------- PERMISO CUSTOM -------------------
class PuedeComprar(BasePermission):
    """Permite comprar varios cursos solo si está autenticado"""
    def has_permission(self, request, view):
        if view.action == 'comprar_varios':
            return request.user.is_authenticated
        return True


# ------------------- VIEWSET -------------------
class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer

    # ------------------- PERMISOS -------------------
    def get_permissions(self):
        """
        Define permisos por acción:
        - alumnos y docentes: solo pueden listar sus compras y comprar
        - admin: CRUD completo
        """
        if self.action in ['comprar_varios', 'list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, DjangoModelPermissions]
        return [perm() for perm in permission_classes]

    # ------------------- QUERYSET -------------------
    def get_queryset(self):
        """
        Admin ve todas las compras, otros solo las suyas
        """
        user = self.request.user
        if user.is_staff:
            return Compra.objects.all()
        return Compra.objects.filter(alumno=user)

    # ------------------- COMPRAR VARIOS -------------------
    @action(detail=False, methods=['post'], url_path='comprar-varios')
    def comprar_varios(self, request):
        alumno = request.user
        curso_ids = request.data.get('curso_ids', [])
        es_trial = request.data.get('es_trial', False)

        if not curso_ids:
            return Response({"error": "No se enviaron cursos"}, status=status.HTTP_400_BAD_REQUEST)

        compras_creadas = []
        errores = []

        for curso_id in curso_ids:
            try:
                curso = Curso.objects.get(id=curso_id)
            except Curso.DoesNotExist:
                errores.append(f"Curso {curso_id} no existe")
                continue

            if Compra.objects.filter(alumno=alumno, curso=curso).exists():
                errores.append(f"Curso {curso.nombre} ya comprado")
                continue

            compra = Compra.objects.create(alumno=alumno, curso=curso, es_trial=es_trial)
            compras_creadas.append(compra)

        serializer = self.get_serializer(compras_creadas, many=True)
        return Response({
            "compras_creadas": serializer.data,
            "errores": errores
        }, status=status.HTTP_201_CREATED)

    # ------------------- RETRIEVE DETALLE -------------------
    def retrieve(self, request, *args, **kwargs):
        """
        GET /compras/<id>/
        - es_trial=True → info limitada de la compra
        - es_trial=False → detalle completo del curso (todas las secciones y lecciones)
        """
        compra = self.get_object()

        if compra.es_trial:
            # Solo info básica de la compra
            serializer = CompraSerializer(compra)
            return Response(serializer.data)
        else:
            # Info completa del curso
            curso_serializer = CursoDetailFullSerializer(compra.curso, context={'request': request})
            data = CompraSerializer(compra).data
            data['curso_detalle_completo'] = curso_serializer.data
            return Response(data)
