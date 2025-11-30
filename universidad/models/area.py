from django.db import models

class Area(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True, null=True)  # nueva descripción
    photo = models.ImageField(
        upload_to='area_portadas/',
        blank=True,
        null=True
    )  # nueva foto

    def __str__(self):
        return self.nombre
