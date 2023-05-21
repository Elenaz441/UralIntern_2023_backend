from .models import *

def get_title_id(object, name_title):
    result = []
    l = list(object)
    for i in l:
        if name_title == 'intern':
            t = i.id_team.id
            a = Team.objects.get(pk=t)
            result.append({'id': t, 'title': a.title})
        else:
            result.append({'id': i.id, 'title': i.title})
    return result


def get_evaluation_criteria_by_stage(id_stage):
    stage = Stage.objects.get(pk=id_stage)
    evaluation_criteria = list(stage.evaluation_criteria.all())
    evaluation_criteria += list(Project.objects.get(pk=stage.id_team.id_project.id).evaluation_criteria.all())
    return list(set(evaluation_criteria))


def get_report(estimations, evaluation_criteria):
    result = []
    for criteria in evaluation_criteria:
        estimations_by_criteria = estimations.filter(id_evaluation_criteria=criteria.id)
        count = len(estimations_by_criteria)
        estimation = 'Нет данных' if count == 0 else sum([i.estimation for i in estimations_by_criteria]) / count
        result.append({'evaluation_criteria': criteria.title, 'estimation': estimation})
    return result


def get_forms_team(id_user, id_team):
    stages = Stage.objects.filter(id_team=id_team, is_active=True)
    total_count = 0
    for stage in stages:
        total_count += len(get_evaluation_criteria_by_stage(stage.id))
    total_count *= len(InternTeam.objects.filter(id_team=id_team))
    user_estimations = len(Estimation.objects.filter(id_appraiser=id_user, id_stage__in=stages))
    return {'not estimated': total_count - user_estimations,
            'estimated': user_estimations,
            'total': total_count}


def get_filter_keys(request) -> dict:
    keys = {}
    if request.query_params.get('id_user'):
        keys["id_appraiser"] = int(request.query_params.get('id_user'))
    if request.query_params.get('id_evaluation_criteria'):
        keys["id_evaluation_criteria"] = int(request.query_params.get('id_evaluation_criteria'))
    if request.query_params.get('id_stage'):
        keys["id_stage"] = int(request.query_params.get('id_stage'))
    if request.query_params.get('id_intern'):
        keys["id_intern"] = int(request.query_params.get('id_intern'))
    return keys