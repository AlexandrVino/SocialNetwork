from django.shortcuts import render
from django.db import transaction
from entities.tools import *
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_exempt
from json import loads
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.backends import ModelBackend
from entities.models import MyUser
from entities.serializers import MyUserSerializers


SESSION = {}


@transaction.atomic
@csrf_exempt
def registration_user(request):
    in_json = request.body
    if not in_json:
        return make_resp({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}}, request)
    in_json = loads(in_json.decode())

    contact_keys = ('github', 'vk', 'facebook', 'instagram', 'twitter', 'website', 'youtube', 'mainLink')

    all_data = in_json.copy()

    all_data['contacts'] = loads(all_data['contacts'])
    for key in contact_keys:
        if all_data['contacts'].get(key, None) is None:
            all_data['contacts'][key] = ''
    all_data['contacts'] = str(all_data['contacts'])

    del all_data['login']
    del all_data['password']

    new_user = MyUser.objects.create_user(username=in_json['login'], **all_data)
    new_user.set_password(in_json['password'])
    new_user.save()

    return make_resp({'resultCode': 0, 'messages': [], 'data': {'userId': new_user.id}}, request)


@transaction.atomic
@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        in_json = request.body
        if not in_json:
            return make_resp({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}}, request)
        in_json = loads(in_json.decode())
        new_user = MyUser.objects.get_by_natural_key(in_json['email'])
        if not new_user.check_password(in_json['password']):
            return make_resp({'resultCode': 1, 'messages': ['User with this login not registered'], 'data': {}}, request)

        login(request, new_user)
        # print(new_user.session)
        key = 0
        for _ in SESSION.keys():
            key += 1
        print(type(new_user))
        SESSION['user'] = new_user

        new_user.save()
        return make_resp({'resultCode': 0, 'messages': [], 'data': {'userId': new_user.id}}, request)
    elif request.method == 'DELETE':
        logout(request)
        del SESSION['user']
        return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
    return make_resp({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}}, request)


@transaction.atomic
def check_authentication(request):

    keys = list(SESSION.keys())
    if not keys:

        in_json = request.body
        if not in_json:
            return make_resp({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}}, request)
        in_json = loads(in_json.decode())

        new_user = authenticate(request, **in_json)
        login(request, new_user)

        return make_resp({'resultCode': 0, 'messages': [], 'data': {'userId': new_user.id}}, request)

    user = SESSION['user']
    return make_resp({'resultCode': 0, 'messages': [], 'data': {'id': user.id,
                                                                'email': user.email,
                                                                'login': user.username}}, request)


@transaction.atomic
def get_profile(request, user_id):
    users = MyUser.objects.all()
    user = [user for user in users if user.id == user_id][0]
    user_json = MyUserSerializers(user).data

    user_json['contacts'] = load_json_from_str(user_json['contacts'])
    user_json['photos'] = load_json_from_str(user_json['photos'])

    return make_resp(user_json, request)


@transaction.atomic
@csrf_exempt
def add_photo(request):
    in_json = request.body
    if not in_json:
        return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)
    print(in_json)

    return make_resp({}, request)


@transaction.atomic
@csrf_exempt
def get_users(request):

    user_args = request.get_raw_uri().split('/users?')[1].split('&')
    user_args = [item.split('=') for item in user_args]
    user_args = {item[0]: int(item[1]) for item in user_args}

    users = MyUser.objects.all()
    users_count = len(users)
    users = users[100 * (user_args['page'] - 1):100 * (user_args['page'] - 1) + user_args['count']]
    users = [MyUserSerializers(user).data for user in users]
    user = SESSION['user']
    for user_json in users:
        user_json['contacts'] = load_json_from_str(user_json['contacts'])
        user_json['photos'] = load_json_from_str(user_json['photos'])
        user_json['name'] = user_json['fullName']
        user_json['followed'] = str(user_json['id']) in user.followers.split(', ')

    return make_resp({'items': users, "totalCount": users_count, "error": None}, request)


@transaction.atomic
@csrf_exempt
def add_friend(request, user_id):
    if request.method == 'POST':
        user = SESSION['user']
        user.followers = ', '.join([follower.strip() for follower in user.followers.split(', ') if follower.strip()] +
                                   [str(user_id)])
        user.save()

        return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
    elif request.method == 'DELETE':
        user = SESSION['user']
        followers = [follower.strip() for follower in user.followers.split(', ') if follower.strip()]
        del followers[followers.index(str(user_id))]
        user.followers = ', '.join(followers)
        user.save()

        return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
    return make_resp({}, request)
