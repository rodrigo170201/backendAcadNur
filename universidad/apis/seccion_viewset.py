from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from universidad.models import Seccion, Curso, Docente


# --- SERIALIZER ---
class SeccionSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)

    nombre = serializers.CharField(required=True)
    descripcion = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Seccion
        fields = ['id', 'nombre', 'descripcion', 'curso', 'curso_nombre']


# --- VIEWSET ---
class SeccionViewSet(viewsets.ModelViewSet):
    queryset = Seccion.objects.all()
    serializer_class = SeccionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    # 🔹 Asignar permisos al crear sección
    def perform_create(self, serializer):
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")

        curso = serializer.validated_data.get('curso')

        # Verificamos que el curso pertenezca al docente autenticado
        if curso.docente != docente:
            raise PermissionDenied("No puedes crear secciones en cursos que no te pertenecen.")

        serializer.save()

    # 🔹 Evitar que un docente edite secciones de cursos ajenos
    def perform_update(self, serializer):
        seccion = self.get_object()
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")

        if seccion.curso.docente != docente:
            raise PermissionDenied("No puedes editar secciones de cursos que no te pertenecen.")

        serializer.save()

    # 🔹 Evitar que un docente elimine secciones de cursos ajenos
    def perform_destroy(self, instance):
        try:
            docente = self.request.user.docente_profile
        except Docente.DoesNotExist:
            raise PermissionDenied("El usuario autenticado no es un docente.")

        if instance.curso.docente != docente:
            raise PermissionDenied("No puedes eliminar secciones de cursos que no te pertenecen.")

        instance.delete()

    # 🔹 Endpoint personalizado: obtener todas las secciones de un curso
    @action(detail=False, methods=['get'], url_path='por_curso/(?P<curso_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def por_curso(self, request, curso_id=None):
        """
        Obtiene todas las secciones de un curso específico (visible para cualquier docente o usuario autenticado).
        """
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({"error": "El curso no existe."}, status=404)

        secciones = Seccion.objects.filter(curso=curso)
        serializer = self.get_serializer(secciones, many=True)
        return Response(serializer.data)
