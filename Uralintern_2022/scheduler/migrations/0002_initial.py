# Generated by Django 3.2.8 on 2023-07-28 10:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('scheduler', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uralapi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='project_id',
            field=models.ForeignKey(db_column='project_id', on_delete=django.db.models.deletion.CASCADE, to='uralapi.project'),
        ),
        migrations.AddField(
            model_name='task',
            name='status_id',
            field=models.ForeignKey(db_column='status_id', on_delete=django.db.models.deletion.CASCADE, to='scheduler.status'),
        ),
        migrations.AddField(
            model_name='task',
            name='team_id',
            field=models.ForeignKey(db_column='team_id', on_delete=django.db.models.deletion.CASCADE, to='uralapi.team'),
        ),
        migrations.AddField(
            model_name='stage',
            name='task_id',
            field=models.ForeignKey(db_column='task_id', on_delete=django.db.models.deletion.CASCADE, to='scheduler.task'),
        ),
        migrations.AddField(
            model_name='executor',
            name='role_id',
            field=models.ForeignKey(db_column='role_id', on_delete=django.db.models.deletion.CASCADE, to='scheduler.role'),
        ),
        migrations.AddField(
            model_name='executor',
            name='task_id',
            field=models.ForeignKey(db_column='task_id', on_delete=django.db.models.deletion.CASCADE, to='scheduler.task'),
        ),
        migrations.AddField(
            model_name='executor',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='task_id',
            field=models.ForeignKey(db_column='task_id', on_delete=django.db.models.deletion.CASCADE, to='scheduler.task'),
        ),
        migrations.AddField(
            model_name='comment',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
