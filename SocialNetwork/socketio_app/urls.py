from socketio_app.views import *
from django.urls import path

urlpatterns = [
    path('', ChatsView.as_view())
]
