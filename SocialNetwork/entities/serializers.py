from rest_framework import serializers
from entities.models import *


class MyUserSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для моего пользователя
    """

    class Meta:
        model = MyUser
        fields = ('userId', 'lookingForAJob', 'lookingForAJobDescription', 'fullName', 'status',
                  'contacts', 'photos', 'id', 'aboutMe')


class PostSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для моего пользователя
    """

    class Meta:
        model = Post
        fields = ('author', 'author_photo', 'image', 'message', 'likes', 'comments', 'reposts')
