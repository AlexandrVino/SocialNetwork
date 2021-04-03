from django.urls import path
from entities.views import *


urlpatterns = [
    path('auth/me', check_authentication),
    path('auth/login', login_user),
    path('auth/registration', registration_user),
    path('profile/<int:user_id>', get_profile),
    path('profile/photo', add_photo),
    path('users', get_users),
    path('follow/<int:user_id>', add_friend)
]
