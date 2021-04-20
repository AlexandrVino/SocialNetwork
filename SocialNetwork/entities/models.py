from django.db import models
from django.contrib.auth.admin import User
from datetime import datetime, timedelta
import jwt
from SocialNetwork.settings import SECRET_KEY


class MyUser(User):
    userId = User.id
    lookingForAJob = models.BooleanField(null=True)
    lookingForAJobDescription = models.CharField(max_length=500, null=True)
    fullName = models.CharField(max_length=100, null=True)

    status = models.CharField(max_length=200, null=True)
    contacts = models.CharField(max_length=500, null=True)

    photos = models.CharField(max_length=5000, null=True)

    followers = models.CharField(max_length=5000, null=True, default='')
    friends = models.CharField(max_length=5000, null=True, default='')

    aboutMe = models.CharField(max_length=500, null=True, default='')
    token = models.CharField(max_length=1000, null=True, default='')

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({
            'id': self.id,
            'email': self.username
        }, SECRET_KEY, algorithm='HS256')
        self.token = token


class Post(models.Model):
    author = models.IntegerField(null=True)
    photo = models.CharField(max_length=5000, null=True)
    image = models.CharField(max_length=5000, null=True)
    text = models.CharField(max_length=5000, null=True)
    likes = models.CharField(max_length=5000, null=True)
    comments = models.CharField(max_length=5000, null=True)
    reposts = models.CharField(max_length=5000, null=True)
