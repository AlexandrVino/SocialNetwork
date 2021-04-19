from django.db import models


# Create your models here.
class ChatRoom(models.Model):
    users = models.CharField(max_length=500, null=True)
    messages = models.CharField(max_length=5000, null=True)

    def add_message(self, mess):
        self.messages = self.messages.split(', ') + [mess.id]


class Message(models.Model):
    author = models.IntegerField(null=True)
    message_id = models.IntegerField(null=True, auto_created=True)
    message_text = models.CharField(max_length=5000, null=True)
    message_images = models.CharField(max_length=5000, null=True)
