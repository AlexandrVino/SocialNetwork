from django.urls import path
from entities.views import *


urlpatterns = [
    path('auth/me', Authentication.as_view()),
    path('auth/login', Authentication.as_view(request_type='login')),
    path('auth/registration', Authentication.as_view(request_type='registration')),

    path('profile', Profile.as_view(request_type='edit_profile_data')),
    path('profile/<int:user_id>', Profile.as_view(request_type='get_profile')),
    path('profile/photo', Profile.as_view(request_type='set_profile_photo')),
    path('profile/status', Profile.as_view(request_type='edit_profile_status')),
    path('profile/friends', Profile.as_view(request_type='get_friends')),
    path('profile/friends/<int:user_id>', Profile.as_view(request_type='add_friend')),
    path('profile/followers', Profile.as_view(request_type='get_followers')),
    path('profile/follow/<int:user_id>', Profile.as_view(request_type='follow')),
    path('profile/posts/<int:post_id>', Profile.as_view(request_type='get_posts')),
    path('profile/post', Profile.as_view(request_type='add_new_post')),
    path('profile/post/<int:post_id>', Profile.as_view(request_type='add_new_post')),

    path('users', Profile.as_view(request_type='get_users'))

]
