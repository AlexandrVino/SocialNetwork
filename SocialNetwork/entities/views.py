from django.shortcuts import render
from django.db import transaction
from entities.tools import *
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_exempt
from json import loads
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.backends import ModelBackend
from entities.models import *
from entities.serializers import *
from random import randint

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response

SESSION = {}


class Authentication(APIView):
    request_type = None
    user = None

    def post(self, request, *args, **kwargs):
        if self.request_type == 'registration':
            try:
                request_json = request.data
                if not request_json:
                    resp = Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}})
                    return make_resp(resp)

                request_json_new = {}
                for key, value in request_json.items():
                    if key == 'photos':
                        request_json_new[key] = value
                    elif key == 'contactsForm':
                        request_json_new['contacts'] = value
                    else:
                        for key_, value_ in value.items():
                            request_json_new[key_] = value_

                request_json = request_json_new.copy()
                print(request_json)

                contact_keys = ('github', 'vk', 'facebook', 'twitter', 'youtube', 'telegram')

                request_json['contacts'] = request_json.get('contacts', {})
                for key in contact_keys:
                    if request_json['contacts'].get(key, None) is None:
                        request_json['contacts'][key] = ''
                request_json['contacts'] = str(request_json['contacts'])

                login_data = {'password': request_json['password'],
                              'username': request_json['login']}
                print(login_data, 1111111)
                del request_json['login']
                del request_json['password']
                del request_json['passwordClone']

                image = {'image': request_json.get('image', None)}
                if image['image']:
                    del request_json['image']
                if any(MyUser.objects.filter(username=login_data['username']).all()):
                    resp = Response({'resultCode': 1, 'messages': ['User with this login has already exists'],
                                     'data': {}})
                    return make_resp(resp)
                try:
                    new_user = MyUser.objects.create_user(username=login_data['username'], **request_json)
                except django.db.utils.IntegrityError:
                    return make_resp({'resultCode': 1, 'messages': ['Incorrect requests'], 'data': {}})
                new_user.set_password(login_data['password'])
                new_user.token = new_user._generate_jwt_token()
                new_user.save()

                login(request, new_user)

                create_folder(path='static/images/users/', folder_name=f'{new_user.id}')

                path = f'static/images/users/{new_user.id}/'
                data = request_json.get('image', None)
                if data is not None:
                    data, file_name = decode_image(data)
                    index = get_count_of_files(path)
                    file_name = file_name.split('.')[0] + f'_{index + 1}.' + file_name.split('.')[1]

                    add_files_in_folder(path=path, files={file_name: data})

                    all_photos = load_json_from_str(new_user.photos, 'photos').get('all', '')
                    base = all_photos if any(all_photos) else []

                    all_photos = base + [f"http://192.168.0.104:8000/{path}{file_name}"]
                    all_data['photos'] = str({"large": f"http://192.168.0.104:8000/{path}{file_name}",
                                              "small": f"http://192.168.0.104:8000/{path}{file_name}",
                                              "all": f"{'; '.join(all_photos)}"})

                resp = Response({'resultCode': 0, 'messages': [], 'data': {'token': new_user.token}})
                return make_resp(resp)
            except KeyError:
                resp = Response({'resultCode': 1, 'messages': ['Incorrect requests'], 'data': {}})
                return make_resp(resp)
        elif self.request_type == 'login':
            request_json = request.data
            if request_json.get('Token', None) is None:
                if not request_json:
                    resp = Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}})
                    return make_resp(resp)

                new_user = MyUser.objects.get_by_natural_key(request_json['email'])
                if not new_user.check_password(request_json['password']):
                    resp = Response({'resultCode': 1, 'messages': ['Incorrect password'], 'data': {}})
                    return make_resp(resp)

                login(request, new_user)
                new_user._generate_jwt_token()
                new_user.save()
                resp = Response({'resultCode': 0, 'token': new_user.token, 'data': {}})
                return make_resp(resp)
            else:
                new_user = authenticate_user(request_json['Token'])
                if any(new_user):
                    login(request, new_user)
                    resp = Response({'resultCode': 0, 'token': request_json['Token'], 'data': {}})
                    return make_resp(resp)
                else:
                    resp = Response({'resultCode': 1, 'messages': [], 'data': {}})
                    return make_resp(resp)

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        user = request.headers.get('Token', None)
        print(user)
        if str(user) != 'AnonymousUser' and user is not None:
            user = authenticate_user(user)
            print(user)
            if user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            resp = Response({'resultCode': 0, 'messages': [], 'data': {'id': user.id,
                                                                       'email': user.email,
                                                                       'login': user.username}})
            return make_resp(resp)
        else:
            resp = Response({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}})
            return make_resp(resp)

    def delete(self, request, *args, **kwargs):
        if self.request_type == 'login':
            user = authenticate_user(request.headers['Token'])
            if user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            user.token = ''
            user.save()
            resp = Response({'resultCode': 0, 'messages': [], 'data': {}})
            return make_resp(resp)


class Profile(APIView):
    request_type = None

    def post(self, request, *args, **kwargs):
        if self.request_type == 'add_friend':
            user_id = int(url_parser(request.get_raw_uri()))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            if str(user_id) in curr_user.followers.split(', '):
                followers = curr_user.followers
                del followers[followers.index(str(user_id))]
                curr_user.followers = ', '.join(followers)
                curr_user.friends = ', '.join(curr_user.friends.split(', ') + [str(user_id)])
                curr_user.save()

                user_ = MyUser.objects.get(id=user_id)
                user_.friends = ', '.join(user_.friends.split(', ') + [str(curr_user.id)])
                user_.save()

                return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        elif self.request_type == 'follow':
            user_id = int(url_parser(request.get_raw_uri()))

            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            curr_user.followers = ', '.join(
                [follower.strip() for follower in user.followers.split(', ') if follower.strip()] +
                [str(user_id)])
            curr_user.save()
        elif self.request_type == 'add_new_post':
            request_json = request.data
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            if not request_json:
                return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))
            data = file_name = None
            post_id = url_parser(request.get_raw_uri())
            try:
                path = f'static/images/posts/{post_id}/'
                data = request_json['image']
                index = get_count_of_files(path)
                file_name = 'profile_photo' + f'_{index + 1}.' + data.name.split('.')[1]
            except KeyError:
                pass
            photos = load_json_from_str(curr_user.photos, 'photos')
            del photos['all']
            post = Post(
                author=curr_user.id,
                author_photo=photos,
                post_text=request_json.get('newPostText', '')
            )

            if data is not None and file_name is not None:
                path = f'static/images/posts/{post.id}/'
                add_files_in_folder(path=path, files={file_name: data})
                post.image = path + f'/{file_name}'
            post.save()
            post = PostSerializers(post).data
            post['author_photo'] = load_json_from_str(post['author_photo'], 'photos')
            post['author'] = MyUser.objects.get(id=post['author']).username
            post['fullName'] = post['author']
            del post['author_photo']['all']
            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': post}))

        return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        if self.request_type == 'get_profile':
            user_id = int(url_parser(request.get_raw_uri()))
            user = MyUser.objects.get(id=user_id)
            user_json = MyUserSerializers(user).data

            user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
            user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
            user_json['is_active'] = user.is_active

            return make_resp(Response(user_json))
        elif self.request_type == 'get_followers':
            curr_user = SESSION.get('user')
            followers = curr_user.followers.split(', ')
            users = MyUser.objects.filter(id in followers).all()
            users = [MyUserSerializers(user).data for user in users]
            users_count = len(users)

            for user_json in users:
                user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
                user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
                user_json['name'] = user_json['fullName']

            return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))
        elif self.request_type == 'get_posts':
            user_id = int(url_parser(request.get_raw_uri()))
            posts = Post.objects.filter(author=user_id).all()
            posts = [PostSerializers(item).data for item in posts]
            for post in posts:
                post['author_photo'] = load_json_from_str(post['author_photo'], 'photos')
                post['author'] = MyUser.objects.get(id=post['author']).username
                post['fullName'] = post['author']
                del post['author_photo']['all']
            return make_resp(Response({'resultCode': 0, 'items': posts}))
        elif self.request_type == 'get_users':
            args = url_parser(request.get_raw_uri())

            users = MyUser.objects.all()
            users_count = len(users)
            first_user_index = args['count'] * (args['page'] - 1)
            last_user_index = args['count'] * (args['page'] - 1) + args['count']

            users = users[first_user_index:last_user_index]
            users = [MyUserSerializers(user).data for user in users]
            user = authenticate_user(request.headers['Token'])
            for user_json in users:
                user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
                user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
                user_json['name'] = user_json['fullName']
                user_json['followed'] = str(user_json['id']) in user.followers.split(', ')
                user_json['name'] = user_json['username'] if not user_json['fullName'] else user_json['fullName']

            return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))
        elif self.request_type == 'get_friends':
            curr_user = SESSION.get('user')
            friends = curr_user.friends.split(', ')
            users = MyUser.objects.filter(id in friends).all()
            users = [MyUserSerializers(user).data for user in users]
            users_count = len(users)

            for user_json in users:
                user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
                user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
                user_json['name'] = user_json['fullName']

            return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))

    def put(self, request, *args, **kwargs):
        if self.request_type == 'edit_profile_data':
            request_json = request.data
            if not request_json:
                return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            curr_user.contacts = str(request_json.get('contacts', curr_user.contacts))
            curr_user.lookingForAJob = str(request_json.get('lookingForAJob', curr_user.lookingForAJob))
            curr_user.lookingForAJobDescription = str(request_json.get('lookingForAJobDescription',
                                                                       curr_user.lookingForAJobDescription))
            curr_user.aboutMe = request_json.get('aboutMe', curr_user.aboutMe)
            curr_user.fullName = request_json.get('fullName', curr_user.fullName)

            curr_user.save()

            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        elif self.request_type == 'set_profile_photo':

            request_json = request.data
            if not request_json:
                return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            path = f'static/images/users/{curr_user.id}/'

            data = request_json['image']
            index = get_count_of_files(path)
            file_name = 'profile_photo' + f'_{index + 1}.' + data.name.split('.')[1]

            data_file = data.read()
            add_files_in_folder(path=path, files={file_name: data_file})

            all_photos = load_json_from_str(curr_user.photos, 'photos').get('all', '')
            base = all_photos if any(all_photos) else []

            all_photos = base + [f"http://192.168.0.104:8000/{path}{file_name}"]
            large_and_small = {"large": f"http://192.168.0.104:8000/{path}{file_name}",
                               "small": f"http://192.168.0.104:8000/{path}{file_name}"}
            curr_user.photos = str({"large": f"http://192.168.0.104:8000/{path}{file_name}",
                                    "small": f"http://192.168.0.104:8000/{path}{file_name}",
                                    "all": f"{'; '.join(all_photos)}"})
            curr_user.save()
            posts = Post.objects.filter(author=curr_user.id).all()
            for post in posts:
                post.author_photo = str(large_and_small)
                post.save()

            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': large_and_small}))
        elif self.request_type == 'edit_profile_status':
            request_json = request.data
            if not request_json:
                return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            curr_user.status = request_json['status']
            curr_user.save()

            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        elif self.request_type == 'add_new_post':
            post_id = int(url_parser(request.get_raw_uri()))
            request_json = request.data
            if not request_json:
                return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))

            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            path = f'static/images/posts/{post_id}/'
            data = request_json.get('image', None)
            if data is not None:
                index = get_count_of_files(path)
                file_name = 'profile_photo' + f'_{index + 1}.' + data.name.split('.')[1]

            post = Post.objects.get(id=post_id)
            data = file_name = None
            # add likes
            if post:
                post.post_text = request_json.get('newPostText', post.post_text)

                if request_json.get('likes', False):
                    all_likes = [load_json_from_str(like_user, 'likes') for like_user in post.likes.split('; ')]
                    base = all_likes if any(all_likes) else []

                    all_likes = base + [str(MyUserSerializers(curr_user).data)]
                    post.likes = '; '.join(all_likes)
            else:
                return make_resp(Response({'resultCode': 1, 'messages': ['Incorrect post id'], 'data': {}}))

            if data is not None and file_name is not None:
                path = f'static/images/posts/{post.id}/'
                add_files_in_folder(path=path, files={file_name: data})
                post.image = path + f'/{file_name}'
            post.save()
            post = PostSerializers(post).data
            post['author_photo'] = load_json_from_str(post['author_photo'], 'photos')
            post['author'] = MyUser.objects.get(id=post['author']).username
            post['fullName'] = post['author']
            del post['author_photo']['all']
            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': post}))

    def delete(self, request, *args, **kwargs):
        if self.request_type == 'add_friend':
            user_id = int(url_parser(request.get_raw_uri()))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            if str(user_id) in curr_user.friends.split(', '):
                friends = curr_user.friends
                del friends[friends.index(str(user_id))]

                curr_user.friends = ', '.join(friends)
                curr_user.followers = ', '.join(curr_user.followers.split(', ') + [str(user_id)])
                curr_user.save()

                user_ = MyUser.objects.get(id=user_id)

                friends = user_.friends
                del friends[friends.index(str(curr_user.id))]

                user_.friends = ', '.join(friends)
                user_.save()

                return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))
        elif self.request_type == 'follow':
            user_id = int(url_parser(request.get_raw_uri()))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            followers = [follower.strip() for follower in curr_user.followers.split(', ') if follower.strip()]
            del followers[followers.index(str(user_id))]
            curr_user.followers = ', '.join(followers)
            curr_user.save()

            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        elif self.request_type == 'add_new_post':
            post_id = int(url_parser(request.get_raw_uri()))
            if post_id is not None:
                post = Post.objects.get(id=post_id)
                if post:
                    post.delete()
                    return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
                return make_resp(Response({'resultCode': 1, 'messages': ['Incorrect post id'], 'data': {}}))
            return make_resp(Response({'resultCode': 1, 'messages': ['Incorrect request'], 'data': {}}))


def authenticate_user(token) -> MyUser:
    user_data = jwt.decode(token, SECRET_KEY, algorithms='HS256')
    try:
        return MyUser.objects.get(id=user_data['id'])
    except KeyError:
        return None
