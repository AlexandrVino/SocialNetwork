from django.db import models
from django.contrib.auth.admin import User


class MyUser(User):
    userId = User.id
    lookingForAJob = models.BooleanField(null=True)
    lookingForAJobDescription = models.CharField(max_length=500, null=True)
    fullName = User.username

    status = models.CharField(max_length=200, null=True)
    contacts = models.CharField(max_length=500, null=True)

    photos = models.CharField(max_length=500, null=True)

    followers = models.CharField(max_length=500, null=True, default='')

