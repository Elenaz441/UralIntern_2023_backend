from django.forms import model_to_dict
from django.shortcuts import render
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Task, Status, Executor, Role, Stage
from uralapi.models import Project, Team, InternTeam, User
from .functions import get_tasks, DATE_FORMAT


class TaskList(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request):
        view_type = request.query_params.get('view_type')
        if view_type not in {'gantt', 'kanban'}:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.groups.filter(name='руководитель').exists():
            projects = Project.objects.all()
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
            task = Task.objects.create(
                parent_id=task_info.get('parent_id'), project_id=team.id_team.id_project,
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
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(model_to_dict(task))


class TaskDetailView(APIView):
    @permission_classes([IsAuthenticated])
    def get(self, request, id):
        task = Task.objects.filter(id=id).select_related('project_id', 'team_id', 'status_id').first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        stages = Stage.objects.filter(task_id=task).values('id', 'task_id', 'description', 'is_ready')
        # TODO: Добавить Комментарии
        return Response({'task': model_to_dict(task), 'stages': stages})

    @permission_classes([IsAuthenticated])
    def put(self, request, id):
        task = Task.objects.filter(id=id).first()
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        task_executors = Executor.objects.filter(task_id=task, user_id=request.user).select_related('user_id').all()
        if not any(executor.user_id == request.user for executor in task_executors):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
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
def change_task_status(request, id):
    pass
