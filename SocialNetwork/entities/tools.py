from django.http import JsonResponse, HttpResponse
import os
from django.core.cache import cache


def make_resp(json, request):
    response = JsonResponse(json)
    response["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response["access-control-allow-headers"] = "Origin, X-Requested-With, Content-Type, Accept, API-KEY"
    response["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["access-control-allow-credentials"] = 'true'
    response["access-control-max-age"] = '300'

    response.session = request.session

    return response


def load_json_from_str(string) -> dict:

    if string:
        string = string[1:-1].split(', ')
        string = [item.split(': ') for item in string]
        string = [item for item in string if any(item)]
        all_photos = string[-1]
        string = {key[1:-1]: value[1:-1] for key, value in string[:-1]}
        string['all'] = all_photos[1][1:-1]
        return string
    return {}


def create_profile_folder(path, user_name):
    user_path = user_name + '/static/images'
    user_path = user_path.split('/')
    for i, folder in enumerate(user_path):
        if i:
            os.mkdir(path + '/'.join(user_path[:i]) + '/' + folder)
        else:
            os.mkdir(path + folder)


def add_files_in_folder(user_path, files):
    data = []
    for key, value in files.items():
        data += [f'{"/".join(user_path.split("/")[1:])}{key}']
        with open(f'{user_path}/{key}', 'wb') as f:
            f.write(value)
    return data


def clear_cache():
    cache.clear()


def url_parser(url) -> dict:
    user_args = url.split('/users?')[1].split('&')
    user_args = [item.split('=') for item in user_args]
    return {item[0]: int(item[1]) for item in user_args}


def decode_image(base_bytes) -> (bytes, str):
    file_name = ''
    try:
        base_bytes[::-1].decode()
    except BaseException as error:
        message = str(error)
        message = message.split('position')[1]
        message = message.split(':')[0].strip()
        base_bytes = base_bytes[:-int(message)]
    try:
        base_bytes.decode()
    except BaseException as error:
        message = str(error)
        message = message.split('position')[1]
        message = message.split(':')[0].strip()
        file_name = str(base_bytes[:int(message)])
        file_name = file_name.split('filename="')[1].split('"')[0].split('.')[-1]
        file_name = 'profile_photo.' + file_name
        base_bytes = base_bytes[int(message):]
    return base_bytes, file_name


def get_count_of_files(directory) -> int:
    for _, _, files in os.walk(directory):
        return len(files)
