from django.db import models
from uralapi.models import User, Team, Project
from django.core.validators import RegexValidator
from datetime import datetime


class Role(models.Model):
    ROLES_CHOICES = [
        ('AUTHOR', 'АВТОР'),
        ('RESPONSIBLE', 'ОТВЕТСТВЕННЫЙ'),
    ]

    id = models.SmallAutoField(verbose_name='ID роли', primary_key=True, auto_created=True)
    name = models.CharField(verbose_name='Название роль', unique=True, max_length=30, choices=ROLES_CHOICES)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Role(id={self.id}, name={self.name})'


class Status(models.Model):
    STATUS_CHOICES = [
        ('TO WORK', 'В РАБОТУ'),
        ('IN PROGRESS', 'ВЫПОЛНЯЕТСЯ'),
        ('TESTING', 'ТЕСТИРОВАНИЕ'),
        ('CHECKING', 'ПРОВЕРКА'),
        ('COMPLETED', 'ЗАВЕРШЕНА'),
        ('OUT OF TIME', 'ПРОСРОЧЕНА')
    ]

    id = models.SmallAutoField(verbose_name='ID статуса', primary_key=True, auto_created=True)
    name = models.CharField(verbose_name='Название статуса', unique=True, null=False, max_length=30,
                            choices=STATUS_CHOICES)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Status(id={self.id}, name={self.name})'

    class Meta:
        db_table = 'statuses'
        verbose_name = 'Статус задачи'
        verbose_name_plural = 'Статусы задач'


class Task(models.Model):
    id = models.BigAutoField(verbose_name='ID задачи', primary_key=True, auto_created=True)
    parent_id = models.ForeignKey('self', null=True, blank=True, verbose_name='Ссылка на родительскую задачу',
                                  on_delete=models.CASCADE, db_column='parent_id', to_field='id')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE, db_column='project_id', to_field='id')
    team_id = models.ForeignKey(Team, on_delete=models.CASCADE, db_column='team_id', to_field='id')
    name = models.CharField(verbose_name='Название задачи', max_length=40, null=False)
    description = models.CharField(verbose_name='Описание задачи', null=True, blank=True, max_length=255)
    is_on_kanban = models.BooleanField(verbose_name='Отображение на канбане', default=True)
    status_id = models.ForeignKey(Status, on_delete=models.CASCADE, db_column='status_id', to_field='id')
    planned_start_date = models.DateField(verbose_name='Время начала задачи')
    planned_final_date = models.DateField(verbose_name='Время окончания задачи')
    deadline = models.DateField(verbose_name='Жесткий дедлайн')
    completed_at = models.DateTimeField(verbose_name='Время завершения', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Время обновления', auto_now=True)

    def update(self, **kwargs):
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        parent_task = self.parent_id
        try:
            start_date = datetime.strptime(kwargs.get('planned_start_date'), "%Y-%m-%d").date()
            final_date = datetime.strptime(kwargs.get('planned_final_date'), "%Y-%m-%d").date()
            deadline = datetime.strptime(kwargs.get('deadline'), "%Y-%m-%d").date()
        except TypeError:
            return self
        if parent_task:
            if parent_task.planned_start_date <= start_date <= final_date <= parent_task.planned_final_date and final_date <= deadline:
                self.planned_start_date = start_date
                self.planned_final_date = final_date
                self.deadline = deadline
            else:
                raise ValueError('Incorrect date terms')
        else:
            if start_date <= final_date <= deadline:
                self.planned_start_date = start_date
                self.planned_final_date = final_date
                self.deadline = deadline
            else:
                raise ValueError('start_date <= final_date <= deadline')
        return self

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Task(id={self.id}, parent_id={self.parent_id}, name={self.name})'

    class Meta:
        db_table = 'tasks'
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class Executor(models.Model):
    id = models.BigAutoField(verbose_name='ID исполнителя', primary_key=True, auto_created=True)
    task_id = models.ForeignKey(Task, on_delete=models.CASCADE, db_column='task_id', to_field='id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', to_field='id')
    role_id = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id', to_field='id')
    time_spent = models.BigIntegerField(verbose_name='Время выполнения задачи в секундах', null=True, blank=True)

    class Meta:
        db_table = 'executors'
        verbose_name = 'Исполнитель задачи'
        verbose_name_plural = 'Исполнители задач'

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Executor(id={self.id}, task_id={self.task_id}, user_id={self.user_id})'


class Stage(models.Model):
    id = models.BigAutoField(verbose_name='ID подэтапа', primary_key=True, auto_created=True)
    task_id = models.ForeignKey(Task, null=False, on_delete=models.CASCADE, db_column='task_id', to_field='id')
    description = models.CharField(verbose_name='Описание этапа', max_length=255)
    is_ready = models.BooleanField(verbose_name='Подэтап выполнен', default=False)
    created_at = models.DateTimeField(verbose_name='Время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Время обновления', auto_now=True)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Stage(id={self.id}, task_id={self.task_id}, description={self.description})'

    class Meta:
        db_table = 'stages'
        verbose_name = 'Подэтап задачи'
        verbose_name_plural = 'Подэтапы задач'


class Comment(models.Model):
    id = models.BigAutoField(verbose_name='ID комментария', primary_key=True, auto_created=True)
    task_id = models.ForeignKey(Task, on_delete=models.CASCADE, db_column='task_id', to_field='id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', to_field='id')
    message = models.CharField(verbose_name='Текст комментария', max_length=255, null=False)
    created_at = models.DateTimeField(verbose_name='Время создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Время обновления', auto_now=True)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Comment(id={self.id}, task_id={self.id}, user_id={self.user_id})'

    class Meta:
        db_table = 'comments'
        verbose_name = 'Комментарий к задаче'
        verbose_name_plural = 'Комментарии к задачам'
