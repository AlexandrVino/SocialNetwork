import requests

server = 'http://192.168.0.104:8001/auth/login'

data = {
    'login': 'SomeOne',
    'password': 'ldflblfdxbrf'
}

response = requests.post(server, json=data)
print(response.json())

