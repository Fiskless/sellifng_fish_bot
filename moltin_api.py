import requests
from environs import Env


def add_product_to_cart(cart_id, product_id, quantity, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
        'Content-Type': 'application/json',
    }

    payload = {"data": {'id': product_id,
                        'type': 'cart_item',
                        'quantity': quantity
                        }
               }

    response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items',
                             headers=headers,
                             json=payload)
    response.raise_for_status()
    return response.json()['data']


def get_cart(chat_id, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{chat_id}/items',
        headers=headers)
    response.raise_for_status()
    return response.json()


def get_products(moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get('https://api.moltin.com/v2/products/',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product(product_id, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_image_url(image_id, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def remove_cart_item(cart_id, product_id, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
    }

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers=headers)
    response.raise_for_status()
    return response.json()['data']


def create_customer(email, moltin_api_token):
    headers = {
        'Authorization': f'Bearer {moltin_api_token}',
        'Content-Type': 'application/json',
    }

    payload = {"data": {'type': 'customer',
                        'name': 'some name',
                        "email": email,
                        "password": "mysecretpassword"
                        }
               }

    response = requests.post('https://api.moltin.com/v2/customers',
                             headers=headers,
                             json=payload)
    response.raise_for_status()
    return response.json()


def get_access_token(moltin_client_id, moltin_client_secret):
    data = {
        'client_id': moltin_client_id,
        'client_secret': moltin_client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token',
                             data=data)
    response.raise_for_status()
    return response.json()['access_token']


if __name__ == '__main__':
    env = Env()
    env.read_env()
    print(get_access_token(env("MOLTIN_CLIENT_ID"), env("MOLTIN_CLIENT_SECRET")))
