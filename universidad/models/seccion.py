from django.db import models
from .curso import Curso

class Seccion(models.Model):
    nombre = models.CharField(max_length=150)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="secciones")
    descripcion = models.TextField(blank=True, null=True)  # 🔹 agregar este campo

    def __str__(self):
        return f"{self.nombre} ({self.curso.nombre})"
