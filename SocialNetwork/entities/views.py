from entities.tools import *
from entities.models import *
from entities.serializers import *

from rest_framework.views import APIView
from rest_framework.response import Response


class PostsView(APIView):
    request_type = None
    user = None

    def post(self, request, *args, **kwargs):
        try:
            if self.request_type == 'add_new_post':
                request_json = request.data
                print(request_json)
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
                    photo=photos,
                    text=request_json.get('newPostText', ''),
                    user_page=int(request_json.get('userPage', curr_user.id))
                )
                print(PostSerializers(post).data)
                if data is not None and file_name is not None:
                    path = f'static/images/posts/{post.id}/'
                    add_files_in_folder(path=path, files={file_name: data})
                    post.image = path + f'/{file_name}'
                post.save()
                post = PostSerializers(post).data
                post['photo'] = load_json_from_str(post['photo'], 'photos')
                post['author'] = MyUser.objects.get(id=post['author']).username
                post['fullName'] = post['author']
                del post['photo']['all']
                return make_resp(Response({'resultCode': 0, 'messages': [], 'data': post}))

            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def put(self, request, *args, **kwargs):
        try:
            if self.request_type == 'add_new_post':
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
                    post.text = request_json.get('newPostText', post.text)

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
                post['photo'] = load_json_from_str(post['photo'], 'photos')
                post['author'] = MyUser.objects.get(id=post['author']).username
                post['fullName'] = post['author']
                del post['photo']['all']
                return make_resp(Response({'resultCode': 0, 'messages': [], 'data': post}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        try:
            user_id = int(url_parser(request.get_raw_uri()))
            posts = Post.objects.filter(user_page=user_id).all()
            posts = [PostSerializers(item).data for item in posts]
            for post in posts:
                post['photo'] = load_json_from_str(post['photo'], 'photos')
                post['author'] = MyUser.objects.get(id=post['author']).username
                del post['photo']['all']
            return make_resp(Response({'resultCode': 0, 'items': posts}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def delete(self, request, *args, **kwargs):
        try:
            if self.request_type == 'add_new_post':
                post_id = int(url_parser(request.get_raw_uri()))
                if post_id is not None:
                    post = Post.objects.get(id=post_id)
                    if post:
                        post.delete()
                        return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
                    return make_resp(Response({'resultCode': 1, 'messages': ['Incorrect post id'], 'data': {}}))
                return make_resp(Response({'resultCode': 1, 'messages': ['Incorrect request'], 'data': {}}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


class UsersView(APIView):
    request_type = None
    user = None

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        try:
            if self.request_type == 'get_users':
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
                    user_json['followed'] = str(user_json['id']) in user.followers.split(', ')
                    user_json['name'] = user_json['username'] if not user_json['fullName'] else user_json['fullName']

                return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


class FollowerView(APIView):
    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def post(self, request, *args, **kwargs):
        try:
            user_id = int(url_parser(request.get_raw_uri()))

            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            curr_user.followers = ', '.join(
                [follower.strip() for follower in user.followers.split(', ') if follower.strip()] +
                [str(user_id)])
            curr_user.save()
            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def get(self, request, *args, **kwargs):
        try:
            curr_user = authenticate_user(request.headers['Token'])
            followers = curr_user.followers.split(', ')
            users = MyUser.objects.filter(id in followers).all()
            users = [MyUserSerializers(user).data for user in users]
            users_count = len(users)

            for user_json in users:
                user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
                user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
                user_json['name'] = user_json['fullName']

            return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def delete(self, request, *args, **kwargs):
        try:
            user_id = int(url_parser(request.get_raw_uri()))
            curr_user = authenticate_user(request.headers['Token'])
            if curr_user is None:
                return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
            followers = [follower.strip() for follower in curr_user.followers.split(', ') if follower.strip()]
            del followers[followers.index(str(user_id))]
            curr_user.followers = ', '.join(followers)
            curr_user.save()

            return make_resp(Response({'resultCode': 0, 'messages': [], 'data': {}}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


class FriendView(APIView):
    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def post(self, request, *args, **kwargs):
        try:
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
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def get(self, request, *args, **kwargs):
        try:
            curr_user = authenticate_user(request.headers['Token'])
            friends = curr_user.friends.split(', ')
            users = MyUser.objects.filter(id in friends).all()
            users = [MyUserSerializers(user).data for user in users]
            users_count = len(users)

            for user_json in users:
                user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
                user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
                user_json['name'] = user_json['fullName']

            return make_resp(Response({'items': users, "totalCount": users_count, "error": None}))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def delete(self, request, *args, **kwargs):
        try:
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
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


class ProfileView(APIView):
    request_type = None

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        try:
            user_id = int(url_parser(request.get_raw_uri()))
            user = MyUser.objects.get(id=user_id)
            user_json = MyUserSerializers(user).data

            user_json['contacts'] = load_json_from_str(user_json['contacts'], 'contacts')
            user_json['photos'] = load_json_from_str(user_json['photos'], 'photos')
            user_json['is_active'] = user.is_active

            return make_resp(Response(user_json))
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def put(self, request, *args, **kwargs):
        try:
            if self.request_type == 'edit_profile_data':
                request_json = request.data
                if not request_json:
                    return make_resp(Response({'resultCode': 1, 'messages': ['Empty request'], 'data': {}}))
                curr_user = authenticate_user(request.headers['Token'])

                if curr_user is None:
                    return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
                if request_json.get('youtube', None) is not None:
                    curr_user.contacts = str(request_json)
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
                    post.photo = str(large_and_small)
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
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))


def authenticate_user(token) -> MyUser:
    try:
        user_data = jwt.decode(token, SECRET_KEY, algorithms='HS256')
        return MyUser.objects.get(id=user_data['id'])
    except BaseException as err:
        logging.warning(err)
        return None
