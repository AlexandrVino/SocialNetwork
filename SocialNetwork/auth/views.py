from entities.tools import *
from django.contrib.auth.hashers import check_password
from entities.models import *
from entities.serializers import *

from rest_framework.views import APIView
from rest_framework.response import Response


class AuthenticationView(APIView):
    request_type = None
    user = None

    def post(self, request, *args, **kwargs):
        try:
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
                    new_user._generate_jwt_token()
                    new_user.save()

                    create_folder(path='static/images/users/', folder_name=f'{new_user.id}')

                    if image['image']:
                        path = f'static/images/users/{curr_user.id}/'

                        data = image['image']
                        index = get_count_of_files(path)
                        file_name = 'profile_photo' + f'_{index + 1}.' + data.name.split('.')[1]

                        data_file = data.read()
                        add_files_in_folder(path=path, files={file_name: data_file})

                        all_photos = load_json_from_str(curr_user.photos, 'photos').get('all', '')
                        base = all_photos if any(all_photos) else []

                        all_photos = base + [f"http://192.168.0.104:8000/{path}{file_name}"]
                        curr_user.photos = str({"large": f"http://192.168.0.104:8000/{path}{file_name}",
                                                "small": f"http://192.168.0.104:8000/{path}{file_name}",
                                                "all": f"{'; '.join(all_photos)}"})
                        curr_user.save()

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

                    new_user._generate_jwt_token()
                    new_user.save()
                    resp = Response({'resultCode': 0, 'token': new_user.token, 'data': {}})
                    return make_resp(resp)
                else:
                    new_user = authenticate_user(request_json['Token'])
                    if new_user is not None:
                        resp = Response({'resultCode': 0, 'token': request_json['Token'], 'data': {}})
                        return make_resp(resp)
                    else:
                        resp = Response({'resultCode': 1, 'messages': [], 'data': {}})
                        return make_resp(resp)
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def options(self, request, *args, **kwargs):
        resp = Response({})
        return make_resp(resp)

    def get(self, request, *args, **kwargs):
        try:
            user = request.headers.get('Token', None)
            if str(user) != 'AnonymousUser' and user is not None:
                user = authenticate_user(user)
                if user is None:
                    return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
                resp = Response({'resultCode': 0, 'messages': [], 'data': {'id': user.id,
                                                                           'email': user.email,
                                                                           'login': user.username}})
                return make_resp(resp)
            else:
                resp = Response({'resultCode': 1, 'messages': ['You are not authentication'], 'data': {}})
                return make_resp(resp)
        except BaseException as err:
            logging.warning(err)
            return make_resp(Response({'resultCode': 1, 'messages': ['WRONG'], 'data': {}}))

    def delete(self, request, *args, **kwargs):
        try:
            if self.request_type == 'login':
                user = authenticate_user(request.headers['Token'])
                if user is None:
                    return make_resp(Response({'resultCode': 1, 'messages': ['Token expired'], 'data': {}}))
                user.token = ''
                user.save()
                resp = Response({'resultCode': 0, 'messages': [], 'data': {}})
                return make_resp(resp)
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
