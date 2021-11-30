import logging
import redis

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from environs import Env
from logs_handler import CustomLogsHandler

from moltin_api_functions import get_products, add_product_to_cart, \
    get_product, get_image_url, get_cart, remove_cart_item, create_customer

_database = None

logger = logging.getLogger('tg_logger')


def add_buttons():
    keyboard = []
    products = get_products()
    for product in products:
        keyboard.append([InlineKeyboardButton(product['name'],
                                              callback_data=product['id'])])

    keyboard.append([InlineKeyboardButton('Корзина',
                                          callback_data='cart_items')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def start(bot, update):

    reply_markup = add_buttons()

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def get_back_to_menu(bot, update):

    query = update.callback_query

    if query.data == "back-to-menu":
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)

        reply_markup = add_buttons()

        query.message.reply_text('Please choose:', reply_markup=reply_markup)
        return "HANDLE_MENU"
    else:
        chat_id = query.message.chat_id
        product_id, product_quantity = query.data.split('/')
        cart_items = add_product_to_cart(chat_id, product_id, int(product_quantity))
        return "HANDLE_DESCRIPTION"


def handle_menu(bot, update):
    query = update.callback_query
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
    if query.data == 'cart_items':
        cart = get_cart(query.message.chat_id)
        cart_info = ''
        for product in cart['data']:
            text = f'''{product['name']}
{product['description']}
{product['meta']['display_price']['with_tax']['unit']['formatted']} per kg
{product['quantity']} kg in cart for {product['meta']['display_price']['with_tax']['value']['formatted']}   

'''
            cart_info = cart_info + text
        cart_price = cart['meta']['display_price']['with_tax']['formatted']
        cart_info = cart_info + f'Total: {cart_price}'

        keyboard = []
        for product in cart['data']:
            keyboard.append([InlineKeyboardButton(
                f'Убрать из корзины {product["name"]}',
                callback_data=product['id'])])

        keyboard.append([InlineKeyboardButton('Назад',
                                              callback_data='back-to-menu')])
        keyboard.append([InlineKeyboardButton('Оплатить',
                                              callback_data='waiting_email')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.send_message(
            chat_id=query.message.chat_id,
            text=cart_info,
            reply_markup=reply_markup
        )
        return "HANDLE_CART"
    else:
        product = get_product(query.data)
        image_id = product['relationships']['main_image']['data']['id']
        text = f'''
{product['name']}
    
{product['meta']['display_price']['with_tax']['formatted']} per kg
100kg on stock     
       
{product['description']}
    '''
        keyboard = [[InlineKeyboardButton("1 кг", callback_data=f'{product["id"]}/1'),
                     InlineKeyboardButton("3 кг", callback_data=f'{product["id"]}/3'),
                     InlineKeyboardButton("5 кг", callback_data=f'{product["id"]}/5')],

                    [InlineKeyboardButton('Назад', callback_data='back-to-menu')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.send_photo(
            chat_id=query.message.chat_id,
            photo=get_image_url(image_id),
            caption=text,
            reply_markup=reply_markup
        )

        return "HANDLE_DESCRIPTION"


def handle_cart(bot, update):
    query = update.callback_query

    if query.data == "waiting_email":
        query.message.reply_text('Пришлите, пожалуйста, ваш email')
        return 'WAITING_EMAIL'
    if query.data == "back-to-menu":
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)

        reply_markup = add_buttons()

        query.message.reply_text('Please choose:', reply_markup=reply_markup)
    else:
        remove_cart_item(query.message.chat_id, query.data)
    return "HANDLE_DESCRIPTION"


def waiting_email(bot, update):
    users_reply = update.message.text
    update.message.reply_text(f'Вы прислали мне эту почту: {users_reply}')
    create_customer(users_reply)

    return 'WAITING_EMAIL'


def handle_users_reply(bot, update):

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
        'HANDLE_DESCRIPTION': get_back_to_menu,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': waiting_email,
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():

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
    chat_id = env("CHAT_ID")
    updater = Updater(token)
    logger.setLevel(logging.WARNING)
    logger.addHandler(CustomLogsHandler(chat_id, token))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()