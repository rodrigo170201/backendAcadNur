from django.db import models
from .seccion import Seccion

class Leccion(models.Model):
    nombre = models.CharField(max_length=150)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name="lecciones")
    material = models.FileField(upload_to='materiales/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.seccion.nombre})"
