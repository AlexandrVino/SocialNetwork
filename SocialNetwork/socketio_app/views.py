# set async_mode to 'threading', 'eventlet', 'gevent' or 'gevent_uwsgi' to
# force a mode else, the best mode is selected automatically from what's
# installed
import os

from django.http import HttpResponse
import socketio
import asyncio
from entities.tools import *
from entities.models import *
from entities.serializers import *
from django.http import JsonResponse
from socketio_app.models import *
from socketio_app.serializers import *
from entities.views import authenticate_user
from rest_framework.views import APIView

async_mode = 'eventlet'
basedir = os.path.dirname(os.path.realpath(__file__))
sio = socketio.Server(async_mode=async_mode)

thread = None


class ChatsView(APIView):
    request_type = None
    user = None

    def options(self, request, *args, **kwargs):
        resp = JsonResponse({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        try:
            curr_user = authenticate_user(request.headers['Token'])
            chats = ChatRoom.objects.all()
            new_chats = []
            for chat in chats:
                if str(curr_user.id) in chat.users.split(', '):
                    new_chats.append(chat)
            chats = new_chats
            response_items = [ChatSerializers(chat).data for chat in chats]
            for chat in response_items:
                mess_ids = chat['messages']
                arr = []
                for mess in Message.objects.all():
                    if str(mess.id) in mess_ids.split(', '):
                        data = MessageSerializers(mess).data
                        author = MyUser.objects.get(id=data['author'])
                        data['photo'] = load_json_from_str(author.photos, 'photos')['large']
                        data['author'] = author.username
                        data['author_id'] = author.id
                        arr += [data]
                chat['messages'] = arr

                arr = []
                users = MyUser.objects.all()
                users = [MyUserSerializers(user).data for user in users]

                for user_json in users:
                    user_js = {}
                    if str(user_json['id']) in chat['users'].split(', '):
                        user_js['photo'] = load_json_from_str(user_json['photos'], 'photos')['large']
                        user_js['fullName'] = user_json['username'] if not user_json['fullName'] \
                            else user_json['fullName']
                        user_js['id'] = user_json['id']
                        arr += [user_js]
                chat['users'] = arr

            resp = JsonResponse({'resultCode': 0, 'messages': [], 'items': response_items})
            return make_resp(resp)

        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


class MyWebSocketServer(socketio.Server):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_database(self):
        pass

    def save_changes(self):
        pass


def background_thread():
    print([*locals(), 1])
    """Example of how to send server generated events to clients."""
    count = 0
    print(count)


@sio.event
def my_event(sid, message):
    print([*locals(), 2])
    sio.emit('my_response', {'data': message['data']}, room=sid)


@sio.event
def my_broadcast_event(sid, message):
    try:
        curr_user = authenticate_user(message['Token'])
        chat_id = message['chat_id']
        try:
            chat = ChatRoom.objects.filter(author=chat_id).first()
            assert chat

        except AssertionError:
            chat = ChatRoom(
                users=message['participants']
            )

        new_message = Message(
            author=curr_user.id,
            message_text=message['data'],
            message_images=message['images']
        )

        chat.add_message(new_message)

        if message.get('images', None) is not None:
            path = f'static/images/chats/{chat.id}/'
            files = {'images': []}
            for key, img_bytes in message['images'].items():
                index = get_count_of_files(path)
                file_name = 'message' + f'_{index + 1}.' + img_bytes.name.split('.')[1]
                add_files_in_folder(path=path, files={file_name: data_file})
                files['images'] += [f"http://192.168.0.104:8000/{files}"]
            files['images'] = ', '.join(files['images'])
            new_message.message_images = str(files)
        new_message.save()

        sio.emit('my_response', MessageSerializers(new_message).data)
    except BaseException as err:
        logging.warning(err)


@sio.event
def join(sid, message):
    print([*locals(), 4])
    try:
        curr_user = authenticate_user(message['Token'])
        chat_id = message['chat_id']

        try:
            chat = ChatRoom.objects.filter(author=chat_id).first()
            assert chat
            chat.users = ', '.join(chat.users.split(', ') + [str(curr_user.id)])

        except AssertionError:
            chat = ChatRoom(
                users=str(curr_user.id)
            )

        chat.save()

        sio.enter_room(sid, message['room'])
        sio.emit('my_response', {'data': 'Entered room: ' + message['room']},
                 room=sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def leave(sid, message):
    try:
        print([*locals(), 5])
        sio.leave_room(sid, message['room'])
        sio.emit('my_response', {'data': 'Left room: ' + message['room']},
                 room=sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def close_room(sid, message):
    try:
        print([*locals(), 6])
        sio.emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.'}, room=message['room'])
        sio.close_room(message['room'])
    except BaseException as err:
        logging.warning(err)


@sio.event
def my_room_event(sid, message):
    try:
        print([*locals(), 7])
        sio.emit('my_response', {'data': message['data']}, room=message['room'])
    except BaseException as err:
        logging.warning(err)


@sio.event
def disconnect_request(sid):
    try:
        print([*locals(), 8])
        sio.disconnect(sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def connect(sid, environ):
    try:
        print([*locals(), 9])
        sio.emit('my_response', {'data': 'Connected', 'count': 0}, room=sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def disconnect(sid):
    try:
        print([sid, 10])
        print('Client disconnected')
    except BaseException as err:
        logging.warning(err)
