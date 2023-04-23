from .models import *

def get_title_id(object, name_title):
    result = []
    l = list(object)
    for i in l:
        if name_title == 'intern':
            t = i.id_team.id
            a = Team.objects.get(pk=t)
            result.append({'id': i.id, 'title': a.title})
        else:
            result.append({'id': i.id, 'title': i.title})
    return result