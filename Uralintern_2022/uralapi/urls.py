from django.urls import path, include
from .views import *
from rest_framework import routers

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

router = routers.SimpleRouter()
router.register(r'team', TeamView)
router.register(r'stage', StageView)

urlpatterns = [
    path('', get_routes),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('user/<int:id>/', get_user),
    path('change-image/<int:id>/', change_user_image),
    path('user-info/<int:pk>/', UpdateInfoView.as_view()),
    path('teams/', get_user_teams),
    path('', include(router.urls)),
    path('evaluation-criteria/', CriteriaView.as_view()),
    path('roles/', RolesView.as_view()),
    path('change-role/', change_role),
    path('project/<int:id_project>/', get_project),
    path('estimate/', estimate),
    path('estimations/<int:id_user>/<int:id_team>/', get_estimations),
    path('estimation/', get_estimation),
    path('forms/<int:id_user>/', get_forms),
    path('forms-for-team/<int:id_user>/<int:id_team>/', get_forms_for_team),
    path('interns-tutors/', get_interns_tutors),
]
