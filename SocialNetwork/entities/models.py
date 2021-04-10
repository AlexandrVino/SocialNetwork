from django.db import models
from django.contrib.auth.admin import User


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


class Post(models.Model):
    author = models.IntegerField()
    author_photo = models.CharField(max_length=5000, null=True)
    image = models.CharField(max_length=5000, null=True)
    post_text = models.CharField(max_length=5000, null=True)
    likes = models.CharField(max_length=5000, null=True)
    comments = models.CharField(max_length=5000, null=True)
    reposts = models.CharField(max_length=5000, null=True)
