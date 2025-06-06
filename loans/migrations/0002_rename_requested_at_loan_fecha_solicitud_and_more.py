# Generated by Django 5.0.4 on 2024-11-28 14:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='loan',
            old_name='requested_at',
            new_name='fecha_solicitud',
        ),
        migrations.RenameField(
            model_name='loan',
            old_name='amount',
            new_name='monto',
        ),
        migrations.RemoveField(
            model_name='loan',
            name='status',
        ),
        migrations.AddField(
            model_name='loan',
            name='aprobado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='loan',
            name='comentario',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='loan',
            name='fecha_aprobacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='loan',
            name='motivo',
            field=models.CharField(default='Sin motivo', max_length=255),
        ),
        migrations.AlterField(
            model_name='loan',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
