from django.shortcuts import render
from django.db import transaction
from entities.tools import *
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_exempt
from json import loads
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.backends import ModelBackend
from entities.models import *
from entities.serializers import MyUserSerializers
from random import randint
SESSION = {}


@transaction.atomic
@csrf_exempt
def registration_user(request):
    in_json = request.body
    if not in_json:
        return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)
    in_json = loads(in_json.decode())
    if not in_json:
        return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)

    contact_keys = ('github', 'vk', 'facebook', 'twitter', 'youtube', 'telegram')

    all_data = in_json.copy()

    all_data['contacts'] = loads(all_data.get('contacts', '{}'))
    for key in contact_keys:
        if all_data['contacts'].get(key, None) is None:
            all_data['contacts'][key] = ''
    all_data['contacts'] = str(all_data['contacts'])

    del all_data['login']
    del all_data['password']

    new_user = MyUser.objects.create_user(username=in_json['login'], **all_data)
    new_user.set_password(in_json['password'])
    new_user.save()
    create_profile_folder(path='data/profiles/', user_name=f'{new_user.id}')

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
            return make_resp({'resultCode': 1, 'messages': ['User with this login not registered'], 'data': {}},
                             request)

        login(request, new_user)
        # print(new_user.session)
        key = 0
        for _ in SESSION.keys():
            key += 1

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

    path = f'static/images/users/{SESSION["user"].id}/'

    data = request.body

    data, file_name = decode_image(data)
    index = get_count_of_files(path)
    file_name = file_name.split('.')[0] + f'_{index + 1}.' + file_name.split('.')[1]

    add_files_in_folder(user_path=path, files={file_name: data})

    all_photos = load_json_from_str(SESSION['user'].photos).get('all', '')

    base = all_photos.split('; ')
    base = base if any(base) else []

    all_photos = base + [f"http://192.168.0.104:8000/{path}{file_name}"]
    SESSION['user'].photos = str({"large": f"http://192.168.0.104:8000/{path}{file_name}",
                                  "small": f"http://192.168.0.104:8000/{path}{file_name}",
                                  "all": f"{'; '.join(all_photos)}"})
    SESSION['user'].save()

    return make_resp({}, request)


@transaction.atomic
@csrf_exempt
def get_users(request):
    args = url_parser(request.get_raw_uri())

    users = MyUser.objects.all()
    users_count = len(users)
    users = users[100 * (args['page'] - 1):100 * (args['page'] - 1) + args['count']]
    users = [MyUserSerializers(user).data for user in users]
    user = SESSION.get('user')
    for user_json in users:
        user_json['contacts'] = load_json_from_str(user_json['contacts'])
        user_json['photos'] = load_json_from_str(user_json['photos'])
        user_json['name'] = user_json['fullName']
        user_json['followed'] = str(user_json['id']) in user.followers.split(', ')

    return make_resp({'items': users, "totalCount": users_count, "error": None}, request)


@transaction.atomic
@csrf_exempt
def follow(request, user_id):
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


@transaction.atomic
@csrf_exempt
def edit_profile_data(request):
    if request.method == 'PUT':
        in_json = request.body
        in_json = loads(in_json.decode())
        if not in_json:
            return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)

        SESSION['user'].contacts = str(in_json['contacts'])
        SESSION['user'].lookingForAJob = in_json['lookingForAJob']
        SESSION['user'].lookingForAJobDescription = in_json['lookingForAJobDescription']
        SESSION['user'].aboutMe = in_json.get('aboutMe', None)
        SESSION['user'].save()

        return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
    return make_resp({}, request)


@transaction.atomic
@csrf_exempt
def edit_profile_status(request):
    if request.method == 'PUT':
        in_json = request.body
        in_json = loads(in_json.decode())
        if not in_json:
            return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)

        SESSION['user'].status = in_json['status']
        SESSION['user'].save()

        return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
    return make_resp({}, request)


@transaction.atomic
@csrf_exempt
def get_followers(request):
    curr_user = SESSION.get('user')

    users = MyUser.objects.all()
    users = [MyUserSerializers(user).data for user in users if str(user.id) in curr_user.followers.split(', ')]
    users_count = len(users)

    for user_json in users:
        user_json['contacts'] = load_json_from_str(user_json['contacts'])
        user_json['photos'] = load_json_from_str(user_json['photos'])
        user_json['name'] = user_json['fullName']

    return make_resp({'items': users, "totalCount": users_count, "error": None}, request)


@transaction.atomic
@csrf_exempt
def get_friends(request):
    curr_user = SESSION.get('user')

    users = MyUser.objects.all()
    users = [MyUserSerializers(user).data for user in users if str(user.id) in curr_user.friends.split(', ')]
    users_count = len(users)

    for user_json in users:
        user_json['contacts'] = load_json_from_str(user_json['contacts'])
        user_json['photos'] = load_json_from_str(user_json['photos'])
        user_json['name'] = user_json['fullName']

    return make_resp({'items': users, "totalCount": users_count, "error": None}, request)


@transaction.atomic
@csrf_exempt
def add_friend(request, user_id):
    if request.method == 'POST':
        if str(user_id) in SESSION['user'].followers.split(', '):
            followers = SESSION['user'].followers
            del followers[followers.index(str(user_id))]

            SESSION['user'].followers = ', '.join(followers)
            SESSION['user'].friends = ', '.join(SESSION['user'].friends.split(', ') + [str(user_id)])
            SESSION['user'].save()

            user_ = MyUser.objects.all()
            user_ = [user for user in user_ if user.id == user_id][0]

            user_.friends = ', '.join(user_.friends.split(', ') + [str(SESSION['user'].id)])
            user_.save()

            return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
        return make_resp({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}, request)
    elif request.method == 'DELETE':
        if str(user_id) in SESSION['user'].friends.split(', '):
            friends = SESSION['user'].friends
            del friends[friends.index(str(user_id))]

            SESSION['user'].friends = ', '.join(friends)
            SESSION['user'].followers = ', '.join(SESSION['user'].followers.split(', ') + [str(user_id)])
            SESSION['user'].save()

            user_ = MyUser.objects.all()
            user_ = [user for user in user_ if user.id == user_id][0]

            friends = user_.friends
            del friends[friends.index(str(SESSION['user'].id))]

            user_.friends = ', '.join(friends)
            user_.save()

            return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
        return make_resp({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}, request)
    return make_resp({}, request)


@transaction.atomic
@csrf_exempt
def add_new_post(request, post_id=None):
    if request.method == 'POST':
        in_json = request.body
        in_json = loads(in_json.decode())
        if not in_json:
            return make_resp({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}, request)

        data, file_name = decode_image(in_json['image'])

        post = Post(
            author=SESSION['user'].id,
            author_photo=SESSION['user'].photos,
            message=in_json.get('message', '')
        )

        path = f'static/images/posts/{post.id}/'
        add_files_in_folder(user_path=path, files={file_name: data})
        post.image = path + f'/{file_name}'

    elif request.method == 'DELETE':
        if post_id is not None:
            post = Post.objects.all()
            post = [item for item in post if item.id == post_id]
            if any(post):
                post = post[0]
                post.delete()
                return make_resp({'resultCode': 0, 'messages': [], 'data': {}}, request)
            return make_resp({'resultCode': 1, 'messages': ['Incorrect post id'], 'data': {}}, request)
        return make_resp({'resultCode': 1, 'messages': ['Incorrect request'], 'data': {}}, request)
    return make_resp({}, request)
