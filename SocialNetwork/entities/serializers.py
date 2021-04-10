from rest_framework import serializers
from entities.models import *


class MyUserSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для моего пользователя
    """

    class Meta:
        model = MyUser
        fields = ('userId', 'lookingForAJob', 'lookingForAJobDescription', 'fullName', 'status',
                  'contacts', 'photos', 'id', 'aboutMe', 'username')


class PostSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для моего пользователя
    """

    class Meta:
        model = Post
        fields = ('id', 'author', 'author_photo', 'image', 'post_text', 'likes', 'comments', 'reposts')
