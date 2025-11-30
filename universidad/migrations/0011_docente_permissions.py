from django.db import migrations

def update_docente_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # Asegurarse de que el grupo Docente exista
    docente_group, created = Group.objects.get_or_create(name='Docente')

    def get_all_perms(model_name):
        codenames = ['view', 'add', 'change', 'delete']
        return [
            Permission.objects.get(codename=f'{code}_{model_name}')
            for code in codenames
            if Permission.objects.filter(codename=f'{code}_{model_name}').exists()
        ]

    def get_view_perm(model_name):
        return Permission.objects.get(codename=f'view_{model_name}')

    # 🔹 Asignar permisos CRUD para seccion, leccion y curso
    all_docente_perms = []
    for model in ['curso', 'seccion', 'leccion']:
        all_docente_perms += get_all_perms(model)

    # 🔹 Permiso solo de visualización para alumnos
    all_docente_perms.append(get_view_perm('alumno'))

    # 🔹 Asignar permisos al grupo Docente
    docente_group.permissions.set(all_docente_perms)
    docente_group.save()

def reverse_func(apps, schema_editor):
    """En caso de revertir la migración"""
    Group = apps.get_model('auth', 'Group')
    docente_group = Group.objects.get(name='Docente')
    docente_group.permissions.clear()

class Migration(migrations.Migration):

    dependencies = [
        ('universidad', '0010_alter_docente_numero_registro'),  # ⚠️ reemplaza con tu última migración real
    ]

    operations = [
        migrations.RunPython(update_docente_permissions, reverse_func),
    ]
