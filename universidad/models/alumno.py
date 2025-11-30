from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import random
import os


def generar_registro():
    return str(random.randint(100000, 999999))


def ruta_foto_perfil(instance, filename):
    # Guardará las fotos dentro de media/alumnos_fotos/<email>/<nombre_archivo>
    return os.path.join('alumnos_fotos', instance.email, filename)


class AlumnoManager(BaseUserManager):
    def create_user(self, email, password, nombre_completo, email_secundario, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        if not email_secundario:
            raise ValueError("El email secundario es obligatorio")
        if not nombre_completo:
            raise ValueError("El nombre completo es obligatorio")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre_completo=nombre_completo,
            email_secundario=email_secundario,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, nombre_completo, email_secundario, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, nombre_completo, email_secundario, **extra_fields)


class Alumno(AbstractBaseUser, PermissionsMixin):
    nombre_completo = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    email_secundario = models.EmailField(unique=True)
    numero_registro = models.CharField(max_length=6, unique=True, default=generar_registro, editable=False)

    # 📸 Imagen de perfil
    photo_profile = models.ImageField(
        upload_to=ruta_foto_perfil,
        blank=True,
        null=True,
        default='alumnos_fotos/profile_icon.png'  # Valor por defecto si no sube imagen
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AlumnoManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre_completo', 'email_secundario']

    def __str__(self):
        return f"{self.nombre_completo} ({self.numero_registro})"
