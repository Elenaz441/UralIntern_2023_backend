# Generated by Django 3.2.8 on 2023-07-13 12:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID комментария')),
                ('message', models.CharField(max_length=255, verbose_name='Текст комментария')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
            ],
            options={
                'verbose_name': 'Комментарий к задаче',
                'verbose_name_plural': 'Комментарии к задачам',
                'db_table': 'comments',
            },
        ),
        migrations.CreateModel(
            name='Executor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID исполнителя')),
                ('time_spent', models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(regex=':[0-9][0-9]:[0-5][0-9]:[0-5][0-9]$')], verbose_name='Время выполнения задачи')),
            ],
            options={
                'verbose_name': 'Исполнитель задачи',
                'verbose_name_plural': 'Исполнители задач',
                'db_table': 'executors',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.SmallAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID роли')),
                ('name', models.CharField(choices=[('AUTHOR', 'АВТОР'), ('RESPONSIBLE', 'ОТВЕТСТВЕННЫЙ')], max_length=30, unique=True, verbose_name='Название роль')),
            ],
            options={
                'verbose_name': 'Роль',
                'verbose_name_plural': 'Роли',
                'db_table': 'roles',
            },
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID подэтапа')),
                ('description', models.CharField(max_length=255, verbose_name='Описание этапа')),
                ('is_ready', models.BooleanField(default=False, verbose_name='Подэтап выполнен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
            ],
            options={
                'verbose_name': 'Подэтап задачи',
                'verbose_name_plural': 'Подэтапы задач',
                'db_table': 'stages',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.SmallAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID статуса')),
                ('name', models.CharField(choices=[('TO WORK', 'В РАБОТУ'), ('IN PROGRESS', 'ВЫПОЛНЯЕТСЯ'), ('TESTING', 'ТЕСТИРОВАНИЕ'), ('CHECKING', 'ПРОВЕРКА'), ('COMPLETED', 'ЗАВЕРШЕНА'), ('OUT OF TIME', 'ПРОСРОЧЕНА')], max_length=30, unique=True, verbose_name='Название статуса')),
            ],
            options={
                'verbose_name': 'Статус задачи',
                'verbose_name_plural': 'Статусы задач',
                'db_table': 'statuses',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID задачи')),
                ('name', models.CharField(max_length=40, verbose_name='Название задачи')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Описание задачи')),
                ('is_on_kanban', models.BooleanField(default=True, verbose_name='Отображение на канбане')),
                ('planned_start_date', models.DateField(verbose_name='Время начала задачи')),
                ('planned_final_date', models.DateField(verbose_name='Время окончания задачи')),
                ('deadline', models.DateField(verbose_name='Жесткий дедлайн')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Время завершения')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
                ('parent_id', models.ForeignKey(blank=True, db_column='parent_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='scheduler.task', verbose_name='Ссылка на родительскую задачу')),
            ],
            options={
                'verbose_name': 'Задача',
                'verbose_name_plural': 'Задачи',
                'db_table': 'tasks',
            },
        ),
    ]
