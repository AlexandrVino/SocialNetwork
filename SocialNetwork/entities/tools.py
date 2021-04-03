from django.http import JsonResponse


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
    string = string[1:-1].split(', ')
    string = [item.split(': ') for item in string]
    string = [item for item in string if any(item)]
    string = {key[1:-1]: value[1:-1] for key, value in string}

    return string

