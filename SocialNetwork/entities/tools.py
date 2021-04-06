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
    if string is not None:
        string = string[1:-1].split(', ')
        string = [item.split(': ') for item in string]
        string = [item for item in string if any(item)]
        string = {key[1:-1]: value[1:-1] for key, value in string}

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


def add_files_in_profile_folder(user_path, files):
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
