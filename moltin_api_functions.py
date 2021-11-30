import requests
from environs import Env

env = Env()
env.read_env()


def add_product_to_cart(cart_id, product_id, quantity):
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
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


def get_cart(chat_id):
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
    }

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{chat_id}/items',
        headers=headers)
    response.raise_for_status()
    return response.json()


def get_products():
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
        'Content-Type': 'application/json',
    }

    response = requests.get('https://api.moltin.com/v2/products/',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product(product_id):
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_image_url(image_id):
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
    }

    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def remove_cart_item(cart_id, product_id):
    headers = {
        'Authorization': f'Bearer {env("MOLTIN_API_TOKEN")}',
    }

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers=headers)
    response.raise_for_status()
    return response.json()['data']