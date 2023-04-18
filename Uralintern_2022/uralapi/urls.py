from django.urls import path, include
from .views import *

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('', get_routes),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/<int:id>', get_user),
    path('user-change/<int:id>', change_user),
    path('user-change-image/<int:id>', change_user_image),
    path('get-user-teams/<int:id_user>', get_user_teams),
    path('get-team/<int:id_team>', get_team),
    path('change-chat/<int:id_team>', change_chat),
    path('estimate/', estimate),
    path('get-estimate/', get_estimate),
    path('get-estimations/<int:id_user>/<int:id_team>', get_estimations),
    path('get-estimation/<int:id_user>/<int:id_team>/<int:id_stage>/<int:id_intern>', get_estimation),
    path('get-stages/<int:id_team>', get_stages),
    path('get-forms/<int:id_user>', get_forms),
    path('get-forms-for-team/<int:id_user>/<int:id_team>', get_forms_for_team)  
]
