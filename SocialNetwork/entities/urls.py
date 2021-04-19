from django.urls import path
from entities.views import *

urlpatterns = [
    path('auth/me', AuthenticationView.as_view()),
    path('auth/login', AuthenticationView.as_view(request_type='login')),
    path('auth/reg', AuthenticationView.as_view(request_type='registration')),

    path('profile', ProfileView.as_view(request_type='edit_profile_data')),
    path('profile/<int:user_id>', ProfileView.as_view(request_type='get_profile')),
    path('profile/photo', ProfileView.as_view(request_type='set_profile_photo')),
    path('profile/status', ProfileView.as_view(request_type='edit_profile_status')),
    path('profile/friends', ProfileView.as_view(request_type='get_friends')),
    path('profile/friends/<int:user_id>', ProfileView.as_view(request_type='add_friend')),
    path('profile/followers', ProfileView.as_view(request_type='get_followers')),
    path('profile/follow/<int:user_id>', ProfileView.as_view(request_type='follow')),
    path('profile/posts/<int:post_id>', ProfileView.as_view(request_type='get_posts')),
    path('profile/post', ProfileView.as_view(request_type='add_new_post')),
    path('profile/post/<int:post_id>', ProfileView.as_view(request_type='add_new_post')),

    path('users', ProfileView.as_view(request_type='get_users'))

]
