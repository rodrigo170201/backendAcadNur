from cloudinary.models import CloudinaryField
from django.db import models
from .seccion import Seccion


class Leccion(models.Model):
    nombre = models.CharField(max_length=150)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name="lecciones")

    material = CloudinaryField(
        'file',
        folder="lecciones/materiales/",
        null=True,
        blank=True,
        resource_type='auto',  # auto detecta imágenes/videos
        type='upload'
    )

    def save(self, *args, **kwargs):
        # Si el archivo es PDF, subir como raw
        if self.material and str(self.material).lower().endswith('.pdf'):
            self.material.resource_type = 'raw'
        super().save(*args, **kwargs)
