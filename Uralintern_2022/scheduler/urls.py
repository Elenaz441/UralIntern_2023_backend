from django.urls import path
from .views import *


urlpatterns = [
    path('api/v1/tasks', TaskList.as_view()),
    path('api/v1/task/<int:id>', TaskDetailView.as_view()),
    path('api/v1/comment', CommentDetailView.as_view()),
    path('api/v1/stage', StageDetailView.as_view()),
    path('api/v1/task/dates/<int:id>', change_date),
    path('api/v1/task/is_on_kanban/<int:id>', change_kanban_view)
]

