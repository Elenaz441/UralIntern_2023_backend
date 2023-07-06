from .models import Task, Executor, Role

GANTT_VALUES_LIST = [
    'id', 'parent_id', 'project_id', 'team_id', 'name',
    'description', 'is_on_kanban', 'status_id__name',
    'planned_start_date', 'planned_final_date', 'deadline'
]

KANBAN_VALUES_LIST = [
    'task_id',
    'task_id__project_id',
    'task_id__team_id__teg',
    'task_id__name',
    'task_id__status_id',
    'task_id__status_id__name',
    'task_id__planned_final_date'
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
    tasks = Executor.objects.select_related('task_id', 'role_id')\
        .filter(task_id__is_on_kanban=True,
                task_id__project_id=project_id,
                role_id=Role.objects.get(name='RESPONSIBLE'))\
        .values(*KANBAN_VALUES_LIST)
    return tasks

