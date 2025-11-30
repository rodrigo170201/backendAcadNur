from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from universidad.apis.alumno_viewset import AlumnoViewSet
from universidad.apis.area_viewset import AreaViewSet
from universidad.apis.compra_viewset import CompraViewSet
from universidad.apis.curso_viewset import CursoViewSet
from universidad.apis.docente_viewset import DocenteViewSet
from universidad.apis.leccion_viewset import LeccionViewSet
from universidad.apis.seccion_viewset import SeccionViewSet
from universidad.apis.user_viewset import UserViewSet, AuthViewSet

router = DefaultRouter()
router.register(r'alumnos', AlumnoViewSet)
router.register(r'docentes', DocenteViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'secciones', SeccionViewSet)
router.register(r'lecciones', LeccionViewSet)
router.register(r'compras', CompraViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
