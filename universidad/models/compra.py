from django.db import models
from .alumno import Alumno
from .curso import Curso

class Compra(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="compras")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="compras")
    fecha_compra = models.DateTimeField(auto_now_add=True)
    es_trial = models.BooleanField(default=False)

    class Meta:
        unique_together = ('alumno', 'curso')  # evita que el mismo alumno compre dos veces el mismo curso

    def __str__(self):
        return f"{self.alumno.nombre_completo} compró {self.curso.nombre}"
