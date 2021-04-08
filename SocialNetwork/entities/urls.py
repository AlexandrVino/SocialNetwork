from django.urls import path
from entities.views import *


urlpatterns = [
    path('auth/me', check_authentication),
    path('auth/login', login_user),
    path('auth/registration', registration_user),

    path('profile', edit_profile_data),
    path('profile/<int:user_id>', get_profile),
    path('profile/photo', add_photo),
    path('profile/status', edit_profile_status),

    path('users', get_users),


    path('friends', get_followers),
    path('friends/<int:user_id>', add_friend),

    path('followers', get_followers),
    path('follow/<int:user_id>', follow),

    path('posts', get_posts),
    path('add_new_post', add_new_post),
    path('add_new_post/<int:post_id>', add_new_post)
]
