"""
Работает с этими модулями:
python-telegram-bot==11.1.0
redis==3.2.1
"""
import os
import logging
import redis
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from environs import Env

_database = None


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


def start(bot, update):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """

    keyboard = []
    products = get_products()
    for product in products:
        keyboard.append([InlineKeyboardButton(product['name'],
                                              callback_data=product['id'])])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def get_back_to_menu(bot, update):

    return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    product = get_product(query.data)
    image_id = product['relationships']['main_image']['data']['id']
    text = f'''
{product['name']}

{product['meta']['display_price']['with_tax']['formatted']} per kg
100kg on stock     
   
{product['description']}
'''
    keyboard = [[InlineKeyboardButton('Назад', callback_data='pressed')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=get_image_url(image_id),
        caption=text,
        reply_markup=reply_markup
    )

    return "HANDLE_DESCRIPTION"


def handle_users_reply(bot, update):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': get_back_to_menu
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = env("REDIS_PASSWORD")
        database_host = env("REDIS_HOST")
        database_port = env("REDIS_PORT")
        _database = redis.Redis(host=database_host, port=database_port,
                                password=database_password)
    return _database


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()