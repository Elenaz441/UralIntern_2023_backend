from django.urls import path
from .views import *


urlpatterns = [
    path('api/v1/tasks', TaskList.as_view()),
    path('api/v1/task/<int:id>', TaskDetailView.as_view()),
    path('api/v1/task/dates/<int:id>', change_date)
]

