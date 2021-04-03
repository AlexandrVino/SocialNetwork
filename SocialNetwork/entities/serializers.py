from abc import ABC

from rest_framework import serializers
from entities.models import MyUser


class MyUserSerializers(serializers.ModelSerializer):
    """
    Сериалайзер для моего пользователя
    """

    class Meta:
        model = MyUser
        fields = ('userId', 'lookingForAJob', 'lookingForAJobDescription', 'fullName', 'status',
                  'contacts', 'photos', 'id')












