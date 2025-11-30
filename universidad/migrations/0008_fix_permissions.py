
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('universidad', '0002_add_roles'),
    ]

    def insert_permissions(apps, schema_editor):
        Group = apps.get_model('auth', 'Group')
        Permission = apps.get_model('auth', 'Permission')

        # Grupos
        admin_group = Group.objects.get(name='Administrador')
        docente_group = Group.objects.get(name='Docente')
        alumno_group = Group.objects.get(name='Alumno')

        # Funciones para obtener permisos
        def get_all_perms(model_name):
            """Retorna todos los permisos CRUD existentes para un modelo"""
            codenames = ['view', 'add', 'change', 'delete']
            return [
                Permission.objects.get(codename=f'{code}_{model_name}')
                for code in codenames
                if Permission.objects.filter(codename=f'{code}_{model_name}').exists()
            ]

        def get_view_perm(model_name):
            """Retorna solo el permiso de ver (view) para un modelo"""
            return Permission.objects.get(codename=f'view_{model_name}')

        # Asignación de permisos
        # Alumno: solo ver
        alumno_group.permissions.set([
            get_view_perm('alumno'),
            get_view_perm('curso'),
            get_view_perm('area')
        ])

        # Docente: CRUD en secciones y lecciones, ver cursos y alumnos
        docente_group.permissions.set(
            [*get_all_perms('seccion'), *get_all_perms('leccion'), *get_all_perms('curso'), get_view_perm('alumno')]
        )

        # Admin: todo
        admin_group.permissions.set(list(Permission.objects.all()))

    operations = [
        migrations.RunPython(insert_permissions, atomic=True),
    ]
