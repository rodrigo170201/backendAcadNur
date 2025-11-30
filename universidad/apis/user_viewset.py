from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from universidad.models import Docente

User = get_user_model()  # Usa tu modelo personalizado Alumno


# ---------------------- SERIALIZADOR ----------------------
class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()  # <-- agregamos este campo

    class Meta:
        model = User
        fields = ('id','photo_profile','email', 'nombre_completo', 'email_secundario', 'numero_registro', 'role')

    def get_role(self, obj):
        # Devuelve el primer grupo del usuario como rol
        grupos = obj.groups.all()
        if grupos.exists():
            return grupos[0].name
        return None


# ---------------------- VISTA DE USUARIO ----------------------
class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Devuelve los datos del usuario autenticado, incluyendo rol"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

        # -----------------------------------------------------------------------
        # ✅ LISTAR ALUMNOS
        # -----------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='listar-alumnos')
    def listar_alumnos(self, request):
        """Lista todos los usuarios que pertenecen al grupo Alumno"""
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo los administradores pueden ver la lista de alumnos.")
        alumnos = User.objects.filter(groups__name='Alumno')
        serializer = UserSerializer(alumnos, many=True)
        return Response(serializer.data)

        # -----------------------------------------------------------------------
        # ✅ LISTAR DOCENTES
        # -----------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='listar-docentes')
    def listar_docentes(self, request):
        """Lista todos los usuarios que pertenecen al grupo Docente"""
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo los administradores pueden ver la lista de docentes.")
        docentes = User.objects.filter(groups__name='Docente')
        serializer = UserSerializer(docentes, many=True)
        return Response(serializer.data)

        # -----------------------------------------------------------------------
        # ✅ LISTAR ADMINISTRADORES
        # -----------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='listar-administradores')
    def listar_administradores(self, request):
        """Lista todos los usuarios que pertenecen al grupo Administrador"""
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo los administradores pueden ver la lista de administradores.")
        admins = User.objects.filter(groups__name='Administrador')
        serializer = UserSerializer(admins, many=True)
        return Response(serializer.data)

# ---------------------- AUTENTICACIÓN Y REGISTRO ----------------------
class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(methods=['post'], detail=False, url_path='register')
    def register(self, request):
        """
        Registro público: solo para alumnos
        """
        nombre_completo = request.data.get('nombre_completo')
        email = request.data.get('email')
        email_secundario = request.data.get('email_secundario')
        password = request.data.get('password')

        if not email or not password or not nombre_completo or not email_secundario:
            return Response({'error': 'Todos los campos son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email,
            password=password,
            nombre_completo=nombre_completo,
            email_secundario=email_secundario
        )

        try:
            alumno_group = Group.objects.get(name='Alumno')
            user.groups.add(alumno_group)
        except Group.DoesNotExist:
            return Response({'error': 'El grupo "Alumno" no existe. Ejecuta la migración de roles primero.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'id': user.id,
            'email': user.email,
            'nombre_completo': user.nombre_completo,
            'rol': 'Alumno'
        }, status=status.HTTP_201_CREATED)

    # -----------------------------------------------------------------------
    # SOLO ADMIN: Crear administradores y docentes
    # -----------------------------------------------------------------------
    @action(methods=['post'], detail=False, url_path='create-admin')
    def create_admin(self, request):
        """Solo administradores pueden crear otros administradores"""
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo los administradores pueden crear otros administradores.")

        # Datos recibidos
        nombre_completo = request.data.get('nombre_completo')
        email = request.data.get('email')
        email_secundario = request.data.get('email_secundario')
        password = request.data.get('password')

        # Validación detallada de campos faltantes
        campos_requeridos = {
            'nombre_completo': nombre_completo,
            'email': email,
            'email_secundario': email_secundario,
            'password': password
        }

        faltantes = [campo for campo, valor in campos_requeridos.items() if not valor]
        if faltantes:
            return Response(
                {'error': f'Faltan los siguientes campos obligatorios: {", ".join(faltantes)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar duplicado de email
        if User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear usuario administrador
        user = User.objects.create_user(
            email=email,
            password=password,
            nombre_completo=nombre_completo,
            email_secundario=email_secundario,
            is_staff=True
        )

        # Asignar grupo Administrador
        try:
            admin_group = Group.objects.get(name='Administrador')
            user.groups.add(admin_group)
        except Group.DoesNotExist:
            return Response(
                {'error': 'El grupo "Administrador" no existe. Ejecuta la migración de roles.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'message': f'Administrador {user.email} creado correctamente.'},
            status=status.HTTP_201_CREATED
        )

    @action(methods=['post'], detail=False, url_path='create-docente')
    def create_docente(self, request):
        """Solo administradores pueden crear docentes"""
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo los administradores pueden crear docentes.")

        nombre_completo = request.data.get('nombre_completo')
        email = request.data.get('email')
        email_secundario = request.data.get('email_secundario')
        password = request.data.get('password')

        if not all([nombre_completo, email, email_secundario, password]):
            return Response({'error': 'Todos los campos son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1️⃣ Crear usuario
        user = User.objects.create_user(
            email=email,
            password=password,
            nombre_completo=nombre_completo,
            email_secundario=email_secundario,
            is_staff=True
        )

        # 2️⃣ Agregar al grupo "Docente"
        try:
            docente_group = Group.objects.get(name='Docente')
            user.groups.add(docente_group)
        except Group.DoesNotExist:
            return Response({'error': 'El grupo "Docente" no existe. Ejecuta la migración de roles.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3️⃣ Crear perfil Docente
        docente = Docente.objects.create(user=user)

        return Response({
            'message': f'Docente {user.email} creado correctamente.',
            'docente_id': docente.id,
            'numero_registro': docente.numero_registro
        }, status=status.HTTP_201_CREATED)