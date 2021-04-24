from django.urls import path
from authentication.views import *

urlpatterns = [
    path('me', AuthenticationView.as_view()),
    path('login', AuthenticationView.as_view(request_type='login')),
    path('reg', AuthenticationView.as_view(request_type='registration'))

]
