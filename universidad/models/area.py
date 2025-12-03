from cloudinary.models import CloudinaryField
from django.db import models

class Area(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True, null=True)  # nueva descripción
    photo = CloudinaryField(
        'image',
        folder="areas/",
        null=True,
        blank=True
    )

    # nueva foto

    def __str__(self):
        return self.nombre
