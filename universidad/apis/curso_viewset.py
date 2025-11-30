from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from universidad.models import Curso, Docente, Seccion, Leccion


# --- SERIALIZERS ---
class LeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leccion
        fields = ['id', 'nombre', 'material']


class SeccionSerializer(serializers.ModelSerializer):
    lecciones = serializers.SerializerMethodField()

    class Meta:
        model = Seccion
        fields = ['id', 'nombre', 'descripcion', 'lecciones']

    def get_lecciones(self, obj):
        # Solo mostramos el material de la primera sección (para usuarios públicos)
        first_section = obj.curso.secciones.order_by('id').first()
        if obj == first_section:
            return LeccionSerializer(obj.lecciones.all(), many=True).data
        else:
            # Solo se muestra el nombre de la lección sin el material
            return [{'id': lec.id, 'nombre': lec.nombre, 'material': None} for lec in obj.lecciones.all()]


class CursoSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    docente_nombre = serializers.CharField(source='docente.user.nombre_completo', read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'descripcion', 'certificable', 'precio',
            'modo_prueba', 'area', 'area_nombre', 'docente_nombre', 'photo_profile'
        ]


class CursoDetailSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    docente_nombre = serializers.CharField(source='docente.user.nombre_completo', read_only=True)
    docente_numero_registro = serializers.CharField(source='docente.numero_registro', read_only=True)
    secciones = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'descripcion', 'certificable', 'precio',
            'modo_prueba', 'area', 'area_nombre', 'docente_nombre', 'docente_numero_registro','photo_profile', 'secciones'
        ]

    def get_secciones(self, obj):
        return SeccionSerializer(obj.secciones.all(), many=True).data


# 🔹 Nuevo Serializer: Detalle completo (docente)
class CursoDetailFullSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    docente_nombre = serializers.CharField(source='docente.user.nombre_completo', read_only=True)
    secciones = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'descripcion', 'certificable', 'precio',
            'modo_prueba', 'area', 'area_nombre', 'docente_nombre', 'photo_profile', 'secciones'
        ]

    def get_secciones(self, obj):
        # Muestra todas las secciones y todas las lecciones con su material
        secciones = obj.secciones.all().prefetch_related('lecciones')
        return [
            {
                'id': s.id,
                'nombre': s.nombre,
                'descripcion': s.descripcion,
                'lecciones': LeccionSerializer(s.lecciones.all(), many=True).data
            }
            for s in secciones
        ]
# --- SERIALIZERS DOCENTE ---
class DocentePublicSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='user.nombre_completo', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    photo_profile = serializers.ImageField(source='user.photo_profile', read_only=True)  # 👈 Corrección clave

    class Meta:
        model = Docente
        fields = ['nombre_completo', 'descripcion', 'numero_registro', 'photo_profile', 'email']

# --- VIEWSET ---
class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_permissions(self):
        """
        Ajusta los permisos según la acción:
        - 'list', 'detalle', 'por_area', 'cursos_docente' → público
        - 'mis_cursos', 'detalle_docente' → docente autenticado
        - crear, editar, eliminar → DjangoModelPermissions
        """
        if self.action in ['list', 'detalle', 'por_area', 'cursos_docente']:
            return [AllowAny()]
        elif self.action in ['mis_cursos', 'detalle_docente']:
            return [IsAuthenticated()]
        return super().get_permissions()

    # Crear curso asignando automáticamente el docente
    def perform_create(self, serializer):
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")
        serializer.save(docente=docente)

    # Evitar que un docente edite cursos ajenos
    def perform_update(self, serializer):
        curso = self.get_object()
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("No puedes editar cursos de otros docentes.")
        if curso.docente != docente:
            raise PermissionDenied("No puedes editar cursos de otros docentes.")
        serializer.save()

    # Evitar que un docente elimine cursos ajenos
    def perform_destroy(self, instance):
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("No puedes eliminar cursos de otros docentes.")
        if instance.docente != docente:
            raise PermissionDenied("No puedes eliminar cursos de otros docentes.")
        instance.delete()

    # Ver cursos del docente logueado
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mis_cursos(self, request):
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")
        cursos = Curso.objects.filter(docente=docente)
        serializer = self.get_serializer(cursos, many=True)
        return Response(serializer.data)

    # Endpoint público: detalle de un curso con secciones y lecciones limitadas
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def detalle(self, request, pk=None):
        try:
            curso = Curso.objects.get(pk=pk)
        except Curso.DoesNotExist:
            return Response({"error": "Curso no existe."}, status=404)
        serializer = CursoDetailSerializer(curso)
        return Response(serializer.data)

    # 🔹 Nuevo endpoint: detalle completo para docente
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def detalle_docente(self, request, pk=None):
        try:
            curso = Curso.objects.get(pk=pk)
        except Curso.DoesNotExist:
            return Response({"error": "Curso no existe."}, status=404)

        # Validar que el docente autenticado sea dueño del curso
        try:
            docente = request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")
        if curso.docente != docente:
            raise PermissionDenied("No puedes acceder a cursos de otros docentes.")

        serializer = CursoDetailFullSerializer(curso)
        return Response(serializer.data)

    # Endpoint público: cursos por área
    @action(detail=False, methods=['get'], url_path='por_area/(?P<area_id>[^/.]+)', permission_classes=[AllowAny])
    def por_area(self, request, area_id=None):
        cursos = Curso.objects.filter(area_id=area_id)
        serializer = self.get_serializer(cursos, many=True)
        return Response(serializer.data)

    # Endpoint público: cursos de un docente específico (por número de registro)
    @action(
        detail=False,
        methods=['get'],
        url_path='docente/(?P<numero_registro>[^/.]+)',
        permission_classes=[AllowAny]
    )
    def cursos_docente(self, request, numero_registro=None):
        try:
            docente = Docente.objects.get(numero_registro=numero_registro)
        except Docente.DoesNotExist:
            return Response({"error": "No existe un docente con ese número de registro."}, status=404)

        # Serializar docente
        docente_data = DocentePublicSerializer(docente).data

        # Serializar cursos
        cursos = Curso.objects.filter(docente=docente)
        cursos_data = self.get_serializer(cursos, many=True).data

        # Respuesta combinada
        return Response({
            "docente": docente_data,
            "cursos": cursos_data
        })

