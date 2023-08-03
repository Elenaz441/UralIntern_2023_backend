from django.db.models import F

from uralapi.models import User
from .models import Task, Executor, Role, Status, Stage
from datetime import datetime

GANTT_VALUES_LIST = [
    'id', 'parent_id', 'project_id', 'team_id', 'name',
    'description', 'is_on_kanban', 'status_id__name',
    'planned_start_date', 'planned_final_date', 'deadline'
]

KANBAN_VALUES_LIST = [
    'task_id',
    'project_id',
    'team__teg',
    'name',
    'status_id',
    'status_id__name',
    'planned_final_date',
    'id_user',
    'user_id__last_name',
    'user_id__first_name',
    'parent_id__name'
]
DATE_FORMAT = "%Y-%m-%d"


def get_tasks(project_id, view_type):
    if view_type == 'gantt':
        tasks = Task.objects.filter(project_id=project_id).all().values(*GANTT_VALUES_LIST)
        return gant_recursive_tasks(tasks, None, [])
    elif view_type == 'kanban':
        return get_kanban_tasks(project_id)
    else:
        return []


def gant_recursive_tasks(initial_tasks_list, parent_id, task_list):
    tasks = list(filter(lambda x: x['parent_id'] == parent_id, initial_tasks_list))
    if not tasks:
        return []
    task_list += tasks
    for task in tasks:
        task['children'] = gant_recursive_tasks(initial_tasks_list, task.get('id'), task.get('children', []))
    return task_list


def get_kanban_tasks(project_id):
    tasks = Executor.objects.select_related('task_id', 'role_id', 'user_id', 'task_id__parent_id') \
        .filter(task_id__is_on_kanban=True,
                task_id__project_id=project_id,
                role_id=Role.objects.get(name='AUTHOR')) \
        .annotate(project_id=F('task_id__project_id'), team__teg=F('task_id__team_id__teg'), name=F('task_id__name'),
                  status_id=F('task_id__status_id'), status_id__name=F('task_id__status_id__name'),
                  parent_id__name=F('task_id__parent_id__name'),
                  planned_final_date=F('task_id__planned_final_date'),
                  id_user=F('user_id_id'),
                  ) \
        .values(*KANBAN_VALUES_LIST)
    return tasks


def create_task(**kwargs) -> Task:
    task = Task(
        parent_id=kwargs.get('parent_id', None),
        project_id=kwargs.get('project_id'),
        team_id=kwargs.get('team_id'),
        name=kwargs.get('name'),
        description=kwargs.get('description'),
        planned_start_date=datetime.strptime(kwargs.get('planned_start_date'), DATE_FORMAT).date(),
        planned_final_date=datetime.strptime(kwargs.get('planned_final_date'), DATE_FORMAT).date(),
        deadline=datetime.strptime(kwargs.get('deadline'), DATE_FORMAT).date(),
        status_id=Status.objects.get(name='TO WORK')
    )
    return task


def create_executors(**kwargs) -> list:
    author = Executor.objects.create(task_id=kwargs.get('task_id'), user_id=kwargs.get('author'),
                                     role_id=Role.objects.get(name='AUTHOR'))
    if kwargs.get('responsible_users'):
        responsible_users = [
            Executor.objects.create(
                task_id=kwargs.get('task_id'),
                user_id=User.objects.get(id=responsible),
                role_id=Role.objects.get(name='RESPONSIBLE')) for responsible in set(kwargs.get('responsible_users')) if responsible]
    else:
        responsible_users = [
            Executor.objects.create(
                task_id=kwargs.get('task_id'),
                user_id=kwargs.get('author'),
                role_id=Role.objects.get(name='RESPONSIBLE'))
        ]
    return [author, *responsible_users]


def create_stages(task, stages):
    if stages:
        return [Stage.objects.create(task_id=task, description=stage.get('description')) for stage in stages]
    return []
