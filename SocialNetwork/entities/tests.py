import requests

server = 'http://192.168.0.104:8000/'

response = requests.get(server + 'posts')
print(response.json())


