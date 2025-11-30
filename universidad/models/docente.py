from django.db import models
from django.contrib.auth import get_user_model
import random

User = get_user_model()

def generar_registro_docente():
    return str(random.randint(100000, 999999))

class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="docente_profile", null=False)
    descripcion = models.TextField(blank=True, null=True)
    numero_registro = models.CharField(max_length=6, unique=True, editable=False)
    photo_profile = models.ImageField(upload_to='docentes_fotos/', blank=True, null=True)  # 🆕 Foto de perfil del docente
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Si no tiene número de registro, copiar del usuario base
        if not self.numero_registro and self.user:
            self.numero_registro = self.user.numero_registro
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.nombre_completo} ({self.numero_registro})"
