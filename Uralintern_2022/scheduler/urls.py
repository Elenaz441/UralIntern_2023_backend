from django.urls import path
from .views import *


urlpatterns = [
    path('api/v1/tasks', TaskList.as_view()),
    path('api/v1/tasks/delete_completed', delete_completed_task),
    path('api/v1/task/<int:id>', TaskDetailView.as_view()),
    path('api/v1/task/<int:id>/dates', change_date),
    path('api/v1/task/<int:id>/status', change_task_status),
    path('api/v1/task/<int:id>/status/complete', complete_task),
    path('api/v1/comment', CommentListView.as_view()),
    path('api/v1/comment/<int:id>', CommentDetailView.as_view()),
    path('api/v1/stage', StageListView.as_view()),
    path('api/v1/stage/<int:id>', StageDetailView.as_view()),
    path('api/v1/task/<int:id>/is_on_kanban', change_kanban_view),
    path('api/v1/user_projects', get_user_projects),
    path('api/v1/project_interns', get_project_info),
    path('api/v1/task/<int:id>/save_timer', save_timer)
]

