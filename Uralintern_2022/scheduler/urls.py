from django.urls import path
from .views import *


urlpatterns = [
    path('api/v1/tasks', TaskList.as_view()),
    path('api/v1/task/<int:id>', TaskDetailView.as_view()),
    path('api/v1/task/<int:id>/dates', change_date),
    path('api/v1/task/<int:id>/status', change_task_status),
    path('api/v1/task/<int:id>/status/complete', complete_task),
    path('api/v1/comment', CommentDetailView.as_view()),
    path('api/v1/stage', StageDetailView.as_view()),
    path('api/v1/task/<int:id>/is_on_kanban', change_kanban_view)
]

