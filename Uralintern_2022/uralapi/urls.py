from django.urls import path, include
from .views import *

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('', get_routes),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('user/<int:id>', get_user),
    path('user-info/<int:pk>', UpdateInfoView.as_view()),
    path('user-change-image/<int:id>', change_user_image),
    path('user-teams/<int:id_user>', get_user_teams),
    path('team/<int:id_team>', get_team),
    path('create-team/', create_team),
    path('change-team/<int:id_team>', change_team),
    path('change-chat/<int:id_team>', change_chat),
    path('estimate/', estimate),
    path('estimations/<int:id_user>/<int:id_team>', get_estimations),
    path('estimation/<int:id_user>/<int:id_evaluation_criteria>/<int:id_stage>/<int:id_intern>', get_estimation),
    path('stages/<int:id_team>', get_stages),
    path('create-stage/', create_stage),
    path('change-stage/<int:id_stage>', change_stage),
    path('forms/<int:id_user>', get_forms),
    path('forms-for-team/<int:id_user>/<int:id_team>', get_forms_for_team),
    path('roles/', get_roles_in_team),
    path('change-role/', change_role),
    path('evaluation-criteria/', get_evaluation_criteria),
    path('project/<int:id_project>', get_project),
]
