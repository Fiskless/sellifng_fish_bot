import requests
from environs import Env


def get_access_token():
    data = {
        'client_id': env("MOLTIN_CLIENT_ID"),
        'client_secret': env("MOLTIN_CLIENT_SECRET"),
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token',
                             data=data)
    response.raise_for_status()
    return response.json()['access_token']


if __name__ == '__main__':
    env = Env()
    env.read_env()
    print(get_access_token())
