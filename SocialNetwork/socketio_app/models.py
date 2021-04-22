from django.db import models


# Create your models here.
class ChatRoom(models.Model):
    id = models.IntegerField(auto_created=True, primary_key=True)
    users = models.CharField(max_length=500, null=True)
    messages = models.CharField(max_length=5000, null=True)

    def add_message(self, mess):
        self.messages = ', '.join(self.messages.split(', ') + [str(mess.id)])
        self.save()


class Message(models.Model):
    author = models.IntegerField(null=True)
    text = models.CharField(max_length=5000, null=True)
    images = models.CharField(max_length=5000, null=True)
