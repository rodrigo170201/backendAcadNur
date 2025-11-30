from django.db import models
from .area import Area
from .docente import Docente

class Curso(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    certificable = models.BooleanField(default=False)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="cursos")
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, related_name="cursos")
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    modo_prueba = models.BooleanField(default=True)  # si tiene sección/lectura libre
    photo_profile = models.ImageField(upload_to='curso_portadas/', blank=True, null=True)  # Nueva foto de portada

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.area.nombre}"
