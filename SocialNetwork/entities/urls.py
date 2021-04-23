from django.urls import path
from entities.views import *

urlpatterns = [

    path('profile', ProfileView.as_view(request_type='edit_profile_data')),
    path('profile/<int:user_id>', ProfileView.as_view()),
    path('profile/photo', ProfileView.as_view(request_type='set_profile_photo')),
    path('profile/status', ProfileView.as_view(request_type='edit_profile_status')),

    path('profile/friends', FriendView.as_view()),
    path('profile/friends/<int:user_id>', FriendView.as_view()),

    path('profile/followers', FollowerView.as_view()),
    path('profile/follow/<int:user_id>', FollowerView.as_view()),

    path('profile/posts/<int:post_id>', PostsView.as_view()),
    path('profile/post', PostsView.as_view(request_type='add_new_post')),
    path('profile/post/<int:post_id>', PostsView.as_view(request_type='add_new_post')),

    path('profile/users', UsersView.as_view(request_type='get_users'))

]
