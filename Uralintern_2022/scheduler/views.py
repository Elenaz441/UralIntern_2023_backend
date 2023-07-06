from rest_framework.decorators import api_view, permission_classes
from uralapi.models import Project, Team, InternTeam, User
from rest_framework.permissions import IsAuthenticated
from .models import Task, Status, Executor, Role, Stage, Comment
from .functions import get_tasks, DATE_FORMAT
from rest_framework.response import Response
from rest_framework.views import APIView
from django.forms import model_to_dict
from rest_framework import status
from datetime import datetime


class TaskList(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request):
        view_type = request.query_params.get('view_type')
        if view_type not in {'gantt', 'kanban'}:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.groups.filter(name='руководитель').exists():
            projects = Project.objects.filter(id_director=request.user).all()
        elif request.user.groups.filter(name='куратор').exists():
            teams = Team.objects.filter(id_tutor=request.user).select_related('id_project')
            projects = {team.id_project for team in teams}
        else:
            intern_team = InternTeam.objects.filter(id_intern=request.user).select_related('id_team').all()
            projects = [team.id_team.id_project for team in intern_team]
        context = [{'project_id': project.id,
                    'title_project': project.title,
                    'tasks': get_tasks(project.id, view_type)} for project in projects]
        return Response(context)

    @permission_classes([IsAuthenticated])
    def post(self, request):
        user = request.user
        task_info = request.data.get('task')
        if not task_info:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        task_stages = request.data.get('task_stages')
        responsible_user_id = request.data.get('responsible_user')
        team = InternTeam.objects.filter(id_intern=user).select_related('id_team').get(
            id_team__id_project=task_info.get('project_id'))
        try:
            parent_task = Task.objects.filter(id=task_info.get('parent_id')).first()
            if parent_task:
                parent_task.is_on_kanban = False
                parent_task.save()
            task = Task.objects.create(
                parent_id=parent_task, project_id=team.id_team.id_project,
                team_id=team.id_team, name=task_info.get('name'), description=task_info.get('description'),
                planned_start_date=task_info.get('planned_start_date'),
                planned_final_date=task_info.get('planned_final_date'),
                deadline=task_info.get('deadline'),
                status_id=Status.objects.get(name='TO WORK'),
            )
            Executor.objects.create(task_id=task, user_id=user, role_id=Role.objects.get(name='AUTHOR'))
            responsible_user = User.objects.filter(id=responsible_user_id).first()
            Executor.objects.create(
                task_id=task, role_id=Role.objects.get(name='RESPONSIBLE'),
                user_id=responsible_user if responsible_user else user
            )
            for stage in task_stages:
                if stage.get('description'):
                    Stage.objects.create(
                        task_id=task,
                        description=stage.get('description')
                    )
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(model_to_dict(task))


class TaskDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request, id):
        task = Task.objects.filter(id=id).select_related('project_id', 'team_id', 'status_id').first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        stages = Stage.objects.filter(task_id=task).values('id', 'task_id', 'description', 'is_ready')
        comments = Comment.objects.filter(task_id=task) \
            .select_related('user_id').values('id', 'task_id', 'user_id_id', 'user_id__first_name', 'user_id__last_name')
        executors = Executor.objects.filter(task_id=task).select_related('role_id', 'user_id') \
            .values('id', 'user_id', 'user_id__first_name', 'user_id__last_name', 'role_id__name')
        return Response({'task': model_to_dict(task),
                         'executors': executors,
                         'stages': stages,
                         'comments': comments})

    @permission_classes([IsAuthenticated])
    def put(self, request, id):
        task = Task.objects.filter(id=id).first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        task_executors = Executor.objects.filter(task_id=task, user_id=request.user).select_related('user_id').all()
        if not any(executor.user_id == request.user for executor in task_executors):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # TODO: Добавить валидацию
        task.update(**request.data)
        return Response(model_to_dict(task))

    @permission_classes([IsAuthenticated])
    def delete(self, request, id):
        task = Task.objects.filter(id=id).first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        author = Executor.objects.filter(task_id=task, role_id=Role.objects.get(name='AUTHOR')).select_related(
            'user_id').first()
        if author.user_id != request.user or not request.user.groups.filter(name='куратор').exists():
            return Response(status.HTTP_405_METHOD_NOT_ALLOWED)
        task.delete()
        return Response({'id': id, 'status': 'deleted'}, status=status.HTTP_200_OK)


class CommentDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def post(self, request):
        task = Task.objects.filter(id=request.data.get('task_id')).first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('message'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        comment = Comment.objects.create(
            task_id=task,
            user_id=request.user,
            message=request.data.get('message')
        )
        return Response(model_to_dict(comment))

    @permission_classes([IsAuthenticated])
    def put(self, request):
        comment = Comment.objects.filter(id=request.data.get('comment_id')).select_related('user_id').first()
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('message'):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if comment.user_id != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        comment.message = request.data.get('message')
        comment.save()
        return Response(model_to_dict(comment))

    @permission_classes([IsAuthenticated])
    def delete(self, request):
        comment = Comment.objects.filter(id=request.data.get('comment_id')).select_related('user_id').first()
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if comment.user_id != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response({'id': request.data.get('comment_id'), 'status': 'deleted'})


class StageDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def post(self, request):
        task = Task.objects.filter(id=request.data.get('task_id')).first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=task.id).all()
        if not any(request.user == executor for executor in executors):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if not request.data.get('description'):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        stage = Stage.objects.create(
            task_id=task,
            description=request.data.get('description')
        )
        return Response(model_to_dict(stage))

    @permission_classes([IsAuthenticated])
    def put(self, request):
        stage = Stage.objects.filter(id=request.data.get('stage_id')).select_related('task_id').first()
        if not stage:
            return Response(status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=stage.task_id).all()
        if not any(request.user == executor for executor in executors):
            return Response(status=status.HTTP_403_FORBIDDEN)
        description, is_ready = request.data.get('description'), request.data.get('is_ready')
        if not (description or is_ready):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if description:
            stage.description = description
        if is_ready:
            stage.is_ready = is_ready
        stage.save()
        return Response(model_to_dict(stage))

    @permission_classes([IsAuthenticated])
    def delete(self, request):
        stage = Stage.objects.filter(id=request.data.get('stage_id')).select_related('task_id').first()
        if not stage:
            return Response(status=status.HTTP_404_NOT_FOUND)
        executors = Executor.objects.filter(task_id=stage.task_id).all()
        if not any(request.user == executor for executor in executors):
            return Response(status=status.HTTP_403_FORBIDDEN)
        stage.delete()
        return Response({'stage_id': request.data.get('stage_id'), 'status': 'deleted'})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_date(request, id):
    task = Task.objects.filter(id=id).select_related('parent_id').first()
    if not task:
        return Response(status=status.HTTP_404_NOT_FOUND)
    start_date, final_date = request.data.get('planned_start_date'), request.data.get('planned_final_date')
    try:
        task.planned_start_date = datetime.strptime(start_date, DATE_FORMAT)
        task.planned_final_date = datetime.strptime(final_date, DATE_FORMAT)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    parent_task = task.parent_id
    if parent_task:
        if parent_task.planned_start_date <= task.planned_start_date < task.planned_final_date <= parent_task.planned_final_date:
            task.save()
            return Response(model_to_dict(task))
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        task.save()
        return Response(model_to_dict(task))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_kanban_view(request, id):
    task = Task.objects.filter(id=id).first()
    if not task:
        return Response(status=status.HTTP_404_NOT_FOUND)
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
    pass
