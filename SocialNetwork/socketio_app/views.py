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
sio = socketio.Server(async_mode=async_mode, cors_allowed_origins=['http://localhost:3000'])

SOCKETSERVERSESSION = []


class ChatsView(APIView):
    request_type = None
    user = None

    def options(self, request, *args, **kwargs):
        resp = JsonResponse({})
        return make_resp(resp, request.get_raw_uri())

    def get(self, request, *args, **kwargs):
        try:
            args = url_parser(request.get_raw_uri())
            if type(args) is not dict:
                curr_user = authenticate_user(request.headers['Token'])
                chats = ChatRoom.objects.all()
                new_chats = []
                for chat in chats:
                    if str(curr_user.id) in chat.users.split(', '):
                        new_chats.append(chat)
                chats = new_chats
                response_items = [ChatSerializers(chat).data for chat in chats]
                for chat in response_items:

                    if len(chat['users'].split(', ')) == 2:

                        chat['lastMessage'] = MessageSerializers(
                            Message.objects.filter(id=chat['messages'].split(', ')[-1]).first()).data
                        user = MyUser.objects.filter(id=[int(us_id) for us_id in chat['users'].split(', ')
                                                         if int(us_id) != curr_user.id][0]).first()
                        us_mess = MyUser.objects.filter(id=int(chat['lastMessage']['author'])).first()
                        chat['lastMessage']['photo'] = load_json_from_str(us_mess.photos, 'photos')['large']
                        chat['lastMessage']['author'] = user.fullName
                        chat['title'] = user.fullName
                        chat['photo'] = load_json_from_str(user.photos, 'photos')['large']
                    else:
                        chat['lastMessage'] = MessageSerializers(
                            Message.objects.filter(id=chat['messages'].split(', ')[-1]).first()).data
                        user = MyUser.objects.filter(id=[int(us_id) for us_id in chat['users'].split(', ')
                                                         if int(us_id) != curr_user.id][0]).first()
                        us_mess = MyUser.objects.filter(id=int(chat['lastMessage']['author'])).first()
                        chat['lastMessage']['photo'] = load_json_from_str(us_mess.photos, 'photos')['large']
                        chat['lastMessage']['author'] = user.fullName
                        chat['photo'] = None
                    del chat['messages']

                resp = JsonResponse({'resultCode': 0, 'messages': [], 'items': response_items})
                return make_resp(resp, request.get_raw_uri())
            else:

                curr_user = authenticate_user(request.headers['Token'])
                chat = ChatRoom.objects.filter(id=args['room']).first()
                sio.start_background_task(background_thread, request=request, chat=chat)
                if len(chat.users.split(', ')) == 2:
                    chat = ChatSerializers(chat).data

                    mess_ids = chat['messages']
                    arr = []
                    for mess in Message.objects.all()[::-1]:
                        if len(arr) >= 10:
                            break
                        if str(mess.id) in mess_ids.split(', '):
                            data = MessageSerializers(mess).data
                            author = MyUser.objects.get(id=data['author'])
                            data['photo'] = load_json_from_str(author.photos, 'photos')['large']
                            data['author'] = author.username
                            data['author_id'] = author.id
                            arr += [data]
                    chat['messages'] = arr[::-1]
                    user = MyUser.objects.filter(id=[int(us_id) for us_id in chat['users'].split(', ')
                                                     if int(us_id) != curr_user.id][0]).first()
                    chat['title'] = user.fullName

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

                    resp = JsonResponse({'resultCode': 0, 'messages': [], 'items': chat})
                    return make_resp(resp, request.get_raw_uri())
                else:
                    chat = ChatSerializers(chat).data
                    mess_ids = chat['messages']
                    arr = []
                    for mess in Message.objects.all()[::-1]:
                        if len(arr) >= 10:
                            break
                        if str(mess.id) in mess_ids.split(', '):
                            data = MessageSerializers(mess).data
                            author = MyUser.objects.get(id=data['author'])
                            data['photo'] = load_json_from_str(author.photos, 'photos')['large']
                            data['author'] = author.username
                            data['author_id'] = author.id
                            arr += [data]
                    chat['messages'] = arr[::-1]

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

                    resp = JsonResponse({'resultCode': 0, 'messages': [], 'items': chat})
                    return make_resp(resp, request.get_raw_uri())

        except BaseException as err:
            print(err)
            logging.warning(err)
            return make_resp(JsonResponse({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}), request.get_raw_uri())


def background_thread(*args, **kwargs):
    request = kwargs['request']
    chat = kwargs['chat']
    curr_user = authenticate_user(request.headers['Token'])
    if curr_user:
        if not any([curr_user.id == user_sess['userId'] for user_sess in SOCKETSERVERSESSION]):
            SOCKETSERVERSESSION.append(
                {
                    'userId': curr_user.id,
                    'sid': None,
                    'chat': chat.id
                }
            )
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        sio.sleep(10)
        count += 1
        sio.emit('response', {'data': 'Server generated event'},
                 namespace='/test')


@sio.event
def sendMessage(sid, message):

    print(sid, message)
    if message.get('room', None) is not None:
        chat = ChatRoom.objects.filter(id=message['room']).first()
        mess = Message(
            author=message['userId'],
            text=message.get('message', None)
        )
    else:

        message_users = ', '.join([str(message['from']), str(message['to'])])
        chat = ChatRoom.objects.filter(users=message_users).first()
        if not chat:
            chat = ChatRoom(
                users=message_users,
                messages=''
            )
        mess = Message(
            author=message['from'],
            text=message.get('message', None)
        )
    mess.save()
    data = message.get('image', False)
    if data:
        path = f'static/docs/chats/{curr_user.id}/'
        index = get_count_of_files(path)
        file_name = 'profile_photo' + f'_{index + 1}.' + data.name.split('.')[1]

        data_file = data.read()
        add_files_in_folder(path=path, files={file_name: data_file})
        mess.save()
    print(mess)
    chat.add_message(mess)

    data = MessageSerializers(mess).data
    author = MyUser.objects.get(id=data['author'])

    for user_sess in SOCKETSERVERSESSION:
        if user_sess['userId'] == author.id:
            user_sess['sid'] = sid
    for user_sess in SOCKETSERVERSESSION:
        if user_sess['chat'] == chat.id:
            if user_sess['sid'] is not None:
                data['photo'] = load_json_from_str(author.photos, 'photos')['large']
                data['author'] = author.username
                data['author_id'] = author.id
                sio.emit('responseSendMessage', {'data': data}, room=user_sess['sid'])


@sio.event
def removeMessage(sid, message):

    chat = ChatRoom.objects.filter(id=message['room']).first()
    messages = chat.messages.split(', ')
    try:
        del messages[messages.index(message['id'])]
        chat.messages = ', '.join(messages)
        chat.save()
    except IndexError:
        pass

    for user_sess in SOCKETSERVERSESSION:
        if user_sess['userId'] == author.id:
            user_sess['sid'] = sid


@sio.event
def editMessage(sid, message):

    mess = Message.objects.filter(id=message['id']).first()
    mess.text = mess.text if message.get('message', None) is None else message.get('message', None)
    mess.image = mess.image if message.get('image', None) is None else message.get('image', None)
    mess.save()

    data = MessageSerializers(mess).data
    author = MyUser.objects.get(id=data['author'])

    for user_sess in SOCKETSERVERSESSION:
        if user_sess['userId'] == author.id:
            user_sess['sid'] = sid
    for user_sess in SOCKETSERVERSESSION:
        if user_sess['chat'] == chat.id:
            if user_sess['sid'] is not None:
                data['photo'] = load_json_from_str(author.photos, 'photos')['large']
                data['author'] = author.username
                data['author_id'] = author.id
                sio.emit('responseSendMessage', {'data': data}, room=user_sess['sid'])


@sio.event
def join(sid, message):
    try:

        curr_user = MyUser.objects.filter(id=message['userId']).first()
        chat_id = message['room']

        if curr_user:
            for user_sess in SOCKETSERVERSESSION:
                if user_sess['userId'] == curr_user.id:
                    user_sess['sid'] = sid

        try:
            chat = ChatRoom.objects.filter(id=int(chat_id)).first()
            assert chat
            members = chat.users.split(', ')
            chat.users = ', '.join(members + ([str(curr_user.id)] if str(curr_user.id) not in members else []))

        except AssertionError:
            chat = ChatRoom(
                users=str(curr_user.id),
                messages=''
            )

        chat.save()

        sio.enter_room(sid, message['room'])
        sio.emit('response', {'data': 'Entered room: ' + message['room']},
                 room=sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def leave(sid, message):
    try:
        print([*locals(), 5])
        sio.leave_room(sid, message['room'])
        sio.emit('response', {'data': 'Left room: ' + message['room']},
                 room=sid)
    except BaseException as err:
        logging.warning(err)


@sio.event
def connect(sid, environ, *args):
    try:
        sio.emit({'resultCode': 0, 'messages': 'connect', 'data': {'room': sid}})
    except BaseException as err:
        print(err)
        logging.warning(err)


@sio.event
def disconnect(sid):
    try:
        for user_sess in SOCKETSERVERSESSION:
            if user_sess['sid'] == sid:
                SOCKETSERVERSESSION.pop(SOCKETSERVERSESSION.index(user_sess))
    except BaseException as err:
        logging.warning(err)
