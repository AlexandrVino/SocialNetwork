from rest_framework import serializers
from socketio_app.models import *


class ChatSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для чата
    """

    class Meta:
        model = ChatRoom
        fields = ('id', 'users', 'messages')


class MessageSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для сообщения
    """

    class Meta:
        model = Message
        fields = ('author', 'id', 'text', 'images')


