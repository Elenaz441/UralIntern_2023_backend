from .functions import get_tasks, DATE_FORMAT, create_task, create_executors, create_stages
from rest_framework.decorators import api_view, permission_classes
from .models import Task, Status, Executor, Role, Stage, Comment
from rest_framework.permissions import IsAuthenticated
from uralapi.models import Project, Team, InternTeam
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.forms import model_to_dict
from rest_framework import status
from django.db.models import F
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_projects(request):
    if request.user.groups.filter(name='руководитель').exists():
        projects = Project.objects.filter(id_director=request.user)
    elif request.user.groups.filter(name='куратор').exists():
        teams = Team.objects.filter(id_tutor=request.user).select_related('id_project')
        projects = {team.id_project for team in teams}
    else:
        intern_teams = InternTeam.objects.filter(id_intern=request.user).select_related('id_team__id_project').all()
        projects = {intern_team.id_team.id_project for intern_team in intern_teams}
    return Response([
        {'id': project.id, 'title': project.title, 'start_date': project.start_date, 'end_date': project.end_date}
        for project in projects
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_project_info(request):
    project_id = int(request.query_params.get('project_id'))
    project = Project.objects.filter(id=project_id).first()
    if not project:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    interns_teams = InternTeam.objects.select_related('id_team__id_project', 'id_team').filter(
        id_team__id_project=project)
    interns = interns_teams.annotate(
        first_name=F('id_intern__first_name'),
        last_name=F('id_intern__last_name')) \
        .values('id_intern', 'first_name', 'last_name')

    teams = Team.objects.filter(id_project=project_id).values('id', 'title', 'teg')
    return Response({'interns': interns, 'teams': teams})


# TODO: TESTED
class TaskList(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request):
        view_type = request.query_params.get('view_type')
        project_id = int(request.query_params.get('project_id'))
        if view_type not in {'gantt', 'kanban'}:
            return Response('Incorrect param for "view_type"', status=status.HTTP_400_BAD_REQUEST)
        project = Project.objects.filter(id=project_id).first()
        if not project:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        assert project.id == project_id
        context = {'project_id': project.id,
                   'title_project': project.title,
                   'tasks': get_tasks(project.id, view_type)}
        return Response(context)

    @permission_classes([IsAuthenticated])
    def post(self, request):
        user = request.user
        task_data = request.data.get('task')
        team = InternTeam.objects.filter(id_intern=user).select_related('id_team').get(
            id_team__id_project=task_data.get('project_id'))
        parent_task = Task.objects.filter(id=task_data.get('parent_id')).first()
        task = create_task(parent_id=parent_task,
                           project_id=team.id_team.id_project,
                           team_id=team.id_team,
                           name=task_data.get('name'),
                           description=task_data.get('description'),
                           planned_start_date=task_data.get('planned_start_date'),
                           planned_final_date=task_data.get('planned_final_date'),
                           deadline=task_data.get('deadline'))
        if parent_task:
            if not (
                    parent_task.planned_start_date <= task.planned_start_date <= task.planned_final_date <= parent_task.planned_final_date):
                return Response('Incorrect date terms', status=status.HTTP_400_BAD_REQUEST)
            parent_task.is_on_kanban = False
            parent_task.save()
        task.save()
        executors = create_executors(task_id=task, author=request.user,
                                     responsible_users=request.data.get('responsible_users'))
        stages = create_stages(task=task, stages=request.data.get('task_stages'))
        return Response({'task': model_to_dict(task),
                         'executors': map(model_to_dict, executors),
                         'stages': map(model_to_dict, stages)})


# TODO: TESTED
class TaskDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request, id):
        task = Task.objects.filter(id=id).select_related('project_id', 'team_id', 'status_id').first()
        if not task:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        stages = Stage.objects.filter(task_id=task).values('id', 'task_id', 'description', 'is_ready')
        comments = Comment.objects.filter(task_id=task) \
            .select_related('user_id') \
            .values('id', 'task_id', 'user_id_id', 'user_id__first_name', 'user_id__last_name', 'message')
        executors = Executor.objects.filter(task_id=task) \
            .select_related('role_id', 'user_id') \
            .values('id', 'user_id', 'user_id__first_name', 'user_id__last_name', 'role_id__name', 'time_spent')
        return Response({'task': model_to_dict(task),
                         'executors': executors,
                         'stages': stages,
                         'comments': comments})

    @permission_classes([IsAuthenticated])
    def put(self, request, id):
        task = Task.objects.filter(id=id).select_related('parent_id').first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        task_executors = Executor.objects.filter(task_id=task).select_related('user_id')
        if not any(executor.user_id == request.user for executor in task_executors):
            return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
        try:
            task = task.update(
                name=request.data.get('name'),
                description=request.data.get('description'),
                planned_start_date=request.data.get('planned_start_date'),
                planned_final_date=request.data.get('planned_final_date'),
                deadline=request.data.get('deadline')
            )
        except ValueError as error_text:
            return Response(error_text.__str__(), status=status.HTTP_400_BAD_REQUEST)
        task.save()
        return Response(model_to_dict(task))

    @permission_classes([IsAuthenticated])
    def delete(self, request, id):
        task = Task.objects.filter(id=id).select_related('parent_id').first()
        if not task:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        author = Executor.objects.filter(task_id=task, role_id=Role.objects.get(name='AUTHOR')) \
            .select_related('user_id').first()
        if author.user_id != request.user and not request.user.groups.filter(name='куратор').exists():
            return Response('Must be task author', status=status.HTTP_403_FORBIDDEN)
        parent_task = task.parent_id
        task.delete()
        tasks = Task.objects.filter(parent_id=parent_task).all()
        if not tasks:
            parent_task.is_on_kanban = True
            parent_task.save()
        return Response({'id': id, 'status': 'deleted'})


# TODO: TESTED
class CommentListView(APIView):
    @permission_classes([IsAuthenticated])
    def post(self, request):
        task = Task.objects.filter(id=request.data.get('task_id')).first()
        if not task:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('message'):
            return Response('Enter "message"', status=status.HTTP_400_BAD_REQUEST)
        comment = Comment.objects.create(
            task_id=task,
            user_id=request.user,
            message=request.data.get('message')
        )
        return Response(model_to_dict(comment))


class CommentDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def put(self, request, id):
        comment = Comment.objects.filter(id=id).select_related('user_id').first()
        if not comment:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('message'):
            return Response('Enter "message"', status=status.HTTP_400_BAD_REQUEST)
        if comment.user_id != request.user:
            return Response('Must be comment owner', status=status.HTTP_403_FORBIDDEN)
        comment.message = request.data.get('message')
        comment.save()
        return Response(model_to_dict(comment))

    @permission_classes([IsAuthenticated])
    def delete(self, request, id):
        comment = Comment.objects.filter(id=id).select_related('user_id').first()
        if not comment:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        if comment.user_id != request.user:
            return Response('Must be comment owner', status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response({'id': request.data.get('comment_id'), 'status': 'deleted'})


class StageListView(APIView):
    @permission_classes([IsAuthenticated])
    def post(self, request):
        task = Task.objects.filter(id=request.data.get('task_id')).first()
        if not task:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=task.id).all()
        if not any(request.user == executor.user_id for executor in executors):
            return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
        if not request.data.get('description'):
            return Response('Enter "description"', status=status.HTTP_400_BAD_REQUEST)
        stage = Stage.objects.create(
            task_id=task,
            description=request.data.get('description')
        )
        return Response(model_to_dict(stage))


# TODO: TESTED
class StageDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def put(self, request, id):
        stage = Stage.objects.filter(id=id).select_related('task_id').first()
        if not stage:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=stage.task_id).all()
        if not any(request.user == executor.user_id for executor in executors):
            return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
        description, is_ready = request.data.get('description'), request.data.get('is_ready')
        if not (description or is_ready):
            return Response('Enter "description" or/and "is_ready', status=status.HTTP_400_BAD_REQUEST)
        if description:
            stage.description = description
        if type(is_ready) is bool and is_ready in {True, False}:
            stage.is_ready = is_ready
        stage.save()
        return Response(model_to_dict(stage))

    @permission_classes([IsAuthenticated])
    def delete(self, request, id):
        stage = Stage.objects.filter(id=id).select_related('task_id').first()
        if not stage:
            return Response('Not found', status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=stage.task_id).all()
        if not any(request.user == executor.user_id for executor in executors):
            return Response("Must be task executor", status=status.HTTP_403_FORBIDDEN)
        stage.delete()
        return Response({'stage_id': request.data.get('stage_id'), 'status': 'deleted'})


# TODO: TESTED
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_date(request, id):
    task = Task.objects.filter(id=id).select_related('parent_id').first()
    if not task:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    executors = Executor.objects.filter(task_id=task).all()
    if not any(request.user == executor.user_id for executor in executors):
        return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
    previous_final_date = task.planned_final_date
    start_date = request.data.get('planned_start_date')
    final_date = request.data.get('planned_final_date')
    deadline = request.data.get('deadline')
    try:
        task.planned_start_date = datetime.strptime(start_date, DATE_FORMAT).date()
        task.planned_final_date = datetime.strptime(final_date, DATE_FORMAT).date()
        if deadline:
            task.deadline = datetime.strptime(deadline, DATE_FORMAT).date()
            if not (task.planned_final_date <= task.deadline):
                raise ValueError('Planned Final Date must be less than Deadline')
        else:
            task.deadline = task.planned_final_date + (task.deadline - previous_final_date)
    except ValueError:
        return Response('Error while parsing dates', status=status.HTTP_400_BAD_REQUEST)
    parent_task = task.parent_id
    if parent_task:
        if parent_task.planned_start_date <= task.planned_start_date <= task.planned_final_date <= parent_task.planned_final_date:
            task.save()
            return Response(model_to_dict(task))
        return Response('Incorrect date terms', status=status.HTTP_400_BAD_REQUEST)
    else:
        task.save()
        return Response(model_to_dict(task))


# TODO: TESTED
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_kanban_view(request, id):
    task = Task.objects.filter(id=id).first()
    if not task:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    child_tasks = Task.objects.filter(parent_id=task.id).all()
    if child_tasks:
        task.is_on_kanban = False
        task.save()
        return Response({'id': task.id, 'is_on_kanban': task.is_on_kanban})
    task.is_on_kanban = not task.is_on_kanban
    task.save()
    return Response({'id': task.id, 'is_on_kanban': task.is_on_kanban})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_task_status(request, id):
    task = Task.objects.filter(id=id).first()
    if not task:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    executors = Executor.objects.select_related('user_id').filter(task_id=task)
    if not any(request.user == executor.user_id for executor in executors):
        return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
    if request.data.get('status') not in ['TO WORK', 'IN PROGRESS', 'TESTING', 'CHECKING', 'COMPLETED']:
        return Response("Bad status", status=status.HTTP_400_BAD_REQUEST)
    _status = Status.objects.filter(name=request.data.get('status')).first()
    task.status_id = _status
    task.save()
    return Response({'id': task.id, 'status_id': task.status_id.id, 'status_name': task.status_id.name})


# TODO: TESTED
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def complete_task(request, id):
    task = Task.objects.filter(id=id).first()
    if not task:
        return Response("Not Found", status=status.HTTP_404_NOT_FOUND)
    responsible = Executor.objects \
        .select_related('user_id', 'role_id') \
        .filter(task_id=task, role_id__name='RESPONSIBLE').first()
    if request.user != responsible.user_id:
        return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
    if not request.data.get('time_spent'):
        return Response('"time_spent" is required', status=status.HTTP_400_BAD_REQUEST)
    try:
        responsible.time_spent = request.data.get('time_spent')
        responsible.save()
    except ValidationError:
        return Response('"time_spent" mist be in "HH:mm:ms" format', status=status.HTTP_400_BAD_REQUEST)
    task.status_id = Status.objects.filter(name='COMPLETED').first()
    task.completed_at = datetime.now()
    task.save()
    return Response({'id': task.id, 'status_id': task.status_id.id, 'status_name': task.status_id.name,
                     'time_spent': responsible.time_spent})


@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def save_timer(request, id):
    task = Task.objects.filter(id=id).first()
    if not task:
        return Response("Not Found", status=status.HTTP_404_NOT_FOUND)
    responsible = Executor.objects.filter(user_id=request.user, task_id=task).first()
    if not responsible:
        return Response('Must be task executor', status=status.HTTP_403_FORBIDDEN)
    try:
        responsible.time_spent = request.data.get('time_spent')
        responsible.save()
    except ValidationError:
        return Response('"time_spent" mist be in "HH:mm:ms" format', status=status.HTTP_400_BAD_REQUEST)
    return Response(model_to_dict(responsible))


@permission_classes([IsAuthenticated])
@api_view(['DELETE'])
def delete_completed_task(request):
    project_id = int(request.query_params.get('project_id'))
    user = request.user
    tasks = Executor.objects.select_related('task_id', 'user_id') \
        .filter(user_id=user,
                role_id__name='AUTHOR',
                task_id__status_id__name='COMPLETED',
                task_id__project_id=project_id
                )
    if not tasks:
        return Response('Nothing to delete')
    context = []
    for el in tasks:
        context.append({'id': el.task_id.id, 'name': el.task_id.name})
        el.task_id.delete()
    return Response(context)
