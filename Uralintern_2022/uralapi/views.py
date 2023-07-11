from datetime import datetime as datetime
import validators
from rest_framework import status
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, mixins

from .models import *
from .serializers import *
from .functions_api import *


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['GET'])
def get_routes(request):
    routes = [
        '/token',
        '/token/refresh',
    ]
    return Response(routes)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view()
@permission_classes([IsAuthenticated])
def get_user(request, id):
    return Response(UserSerializer(User.objects.get(pk=id)).data)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def change_user_image(request, id):
    if request.user.id != id:
        return Response(status=status.HTTP_403_FORBIDDEN)
    user = User.objects.get(pk=id)
    user.image = request.data['image']
    user.save()
    return Response(UserSerializer(user).data)


@permission_classes([IsAuthenticated])
class UpdateInfoView(generics.RetrieveUpdateAPIView):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer


@api_view()
@permission_classes([IsAuthenticated])
def get_user_teams(request):
    intern_teams = get_title_id(InternTeam.objects.filter(id_intern=request.user.id), 'intern')
    tutor_teams = get_title_id(Team.objects.filter(id_tutor=request.user.id), 'tutor')
    director_teams = get_title_id(Project.objects.filter(id_director=request.user.id,
                                                         start_date__lte=datetime.datetime.today(),
                                                         end_date__gte=datetime.datetime.today()), 'director')
    return Response({'intern': intern_teams, 'tutor': tutor_teams, 'director': director_teams})


@permission_classes([IsAuthenticated])
class TeamView(mixins.ListModelMixin, mixins.RetrieveModelMixin,
               mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_queryset(self):
        id_project = self.request.query_params.get('id_project')
        queryset = Team.objects.all()
        if id_project:
            queryset = queryset.filter(id_project=int(id_project))
        return queryset


@permission_classes([IsAuthenticated])
class StageView(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin, mixins.ListModelMixin,
                mixins.DestroyModelMixin, GenericViewSet):
    queryset = Stage.objects.all()
    serializer_class = StageSerializer

    def get_queryset(self):
        id_team = self.request.query_params.get('id_team')
        queryset = Stage.objects.filter(is_active=True)
        if id_team:
            queryset = queryset.filter(id_team=int(id_team))
        return queryset


@permission_classes([IsAuthenticated])
class CriteriaView(generics.ListAPIView):
    queryset = EvaluationCriteria.objects.all()
    serializer_class = EvaluationCriteriaSerializer


@permission_classes([IsAuthenticated])
class RolesView(generics.ListAPIView):
    queryset = RoleInTeam.objects.all()
    serializer_class = RoleInTeamSerializer


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_role(request):
    data = request.data
    if data['id_intern'] != request.user.id:
        return Response(status=status.HTTP_403_FORBIDDEN)
    instance_role = InternTeam.objects.filter(id_intern=data['id_intern'], id_team=data['id_team']).first()
    if not instance_role:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = InternTeamSerializer(instance=instance_role, data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view()
@permission_classes([IsAuthenticated])
def get_project(request, id_project):
    project = ProjectSerializer(Project.objects.get(pk=id_project)).data
    project['teams'] = TeamSerializer(Team.objects.filter(id_project=id_project), many=True).data
    return Response(project)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimate(request, *args, **kwargs):
    estimation = request.data
    estimation['id_appraiser'] = request.user.id
    # пробуем получить оценку, если есть, то обновить существующую, если None, то создать новую
    instance_estimation = Estimation.objects.select_related('id_appraiser', 'id_intern', 'id_stage',
                                                            'id_evaluation_criteria') \
        .filter(id_appraiser=estimation['id_appraiser'], id_intern=estimation['id_intern'],
                id_stage=estimation['id_stage'], id_evaluation_criteria=estimation['id_evaluation_criteria']).first()
    # операция обновления стоит дороже
    serializer = EstimationSerializer(instance_estimation, data=estimation) if instance_estimation else \
        EstimationSerializer(data=estimation)

    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view()
@permission_classes([IsAuthenticated])
def get_estimation(request, *args, **kwargs):
    if not (request.query_params.get('id_user') or
            request.query_params.get('id_evaluation_criteria') or
            request.query_params.get('id_stage') or
            request.query_params.get('id_intern')):
        return Response(status=status.HTTP_400_BAD_REQUEST)
    # if int(request.user.id) != int(request.query_params.get('id_user')):
    #     return Response(status=status.HTTP_403_FORBIDDEN)
    estimation = Estimation.objects.filter(**get_filter_keys(request))
    if estimation:
        return Response(EstimationSerializer(estimation, many=True).data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view()
@permission_classes([IsAuthenticated])
def get_estimations(request, id_user, id_team):
    if request.user.id != id_user and \
            request.user.id != Team.objects.get(id=id_team).id_tutor.id and \
            not InternTeam.objects.filter(id_intern=request.user.id, id_team=id_team):
        return Response(status=status.HTTP_403_FORBIDDEN)
    stages = Stage.objects.filter(id_team=id_team)
    evaluation_criteria = [get_evaluation_criteria_by_stage(stage.id) for stage in stages]
    evaluation_criteria = list(set([item for sublist in evaluation_criteria for item in sublist]))
    self_estimations = Estimation.objects.filter(id_appraiser=id_user, id_stage__in=list(stages), id_intern=id_user)
    self_estimation = get_report(self_estimations, evaluation_criteria)
    team_estimations = Estimation.objects.filter(~Q(id_appraiser=id_user), id_stage__in=list(stages), id_intern=id_user)
    team_estimation = get_report(team_estimations, evaluation_criteria)
    total_estimations = Estimation.objects.filter(id_stage__in=list(stages), id_intern=id_user)
    total_estimation = get_report(total_estimations, evaluation_criteria)
    return Response({'total_estimation': total_estimation,
                     'self_estimation': self_estimation,
                     'team_estimation': team_estimation})


@api_view()
@permission_classes([IsAuthenticated])
def get_forms(request, id_user):
    if request.user.id != int(id_user):
        Response(status=status.HTTP_403_FORBIDDEN)
    teams = Team.objects.filter(id_tutor=id_user)
    result = {'not estimated': 0, 'estimated': 0, 'total': 0}
    for team in teams:
        forms = get_forms_team(id_user, team.id)
        result['not estimated'] += forms['not estimated']
        result['estimated'] += forms['estimated']
        result['total'] += forms['total']
    intern_team = InternTeam.objects.filter(id_intern=id_user)
    for team in intern_team:
        forms = get_forms_team(id_user, team.id_team)
        result['not estimated'] += forms['not estimated']
        result['estimated'] += forms['estimated']
        result['total'] += forms['total']
    return Response(result)


@api_view()
@permission_classes([IsAuthenticated])
def get_forms_for_team(request, id_user, id_team):
    if request.user.id != int(id_user):
        Response(status=status.HTTP_403_FORBIDDEN)
    return Response(get_forms_team(id_user=id_user, id_team=id_team))


@api_view()
@permission_classes([IsAuthenticated])
def get_interns_tutors(request):
    if not User.objects.get(pk=request.user.id).groups.filter(name='руководитель'):
        Response(status=status.HTTP_403_FORBIDDEN)
    tutors = User.objects.filter(groups__in=[Group.objects.get(name='куратор').id])
    interns = User.objects.filter(groups__in=[Group.objects.get(name='стажёр').id])
    return Response({'tutors': UserSerializer(tutors, many=True).data,
                     'interns': UserSerializer(interns, many=True).data})