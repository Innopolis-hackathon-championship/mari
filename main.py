import telebot
from segno import*
from telebot import types
import random
import sqlite3
import webbrowser
import string
from config import Config
import asyncio
indificator = None


m = ["doedo.inno", "edjfi.inno", "feodo.inno"]
soup = ["Соляночка",'- 34 руб.', "Борщик",'- 56 руб.']
basic = ["Котлеточка",'- 45 руб.',"Биточки",'- 90 руб.']
garnish = ["Пюрешочки",'- 13 руб.', "Греча",'- 15 руб.']
drinks = ["Компотик",'- 12 руб.', "Чаечек",'- 14 руб.']

bot = telebot.TeleBot(token=Config.token)
indif = None

class UserQueue:
    def __init__(self):
        self.queue = []

    def enqueue(self, user_id):
        if user_id not in self.queue:
            self.queue.append(user_id)

    def dequeue(self):
        if self.is_empty():
            return None
        return self.queue.pop(0)

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)

    def display_queue(self):
        if self.is_empty():
            return "Очередь пуста."
        queue_message = "Текущая очередь:\n"
        for idx, user_id in enumerate(self.queue, start=1):
            queue_message += f'{idx}. {user_id}\n'
        return queue_message

    def remove_user(self, user_id):
        if user_id in self.queue:
            self.queue.remove(user_id)

    def notify_first_user(self):
        if not self.is_empty():
            first_user_id = self.queue[0]
            bot.send_message(first_user_id, 'Вы первый в очереди! Пожалуйста, подойдите.')

user_queue = UserQueue()

@bot.message_handler(commands=['enqueue'])
def enqueue_user(message):
    user_id = message.from_user.first_name

    # Проверяем, заполнена ли корзина пользователя
    if not cart.items:
        bot.reply_to(message, 'Чтобы встать в очередь, сначала добавьте товары в корзину.')
        return

    user_queue.enqueue(user_id)
    bot.reply_to(message, f'Вы добавлены в очередь.')
    user_queue.notify_first_user()
@bot.message_handler(commands=['dequeue'])
def dequeue_user(message):
    user_id = user_queue.dequeue()
    if user_id is None:
        bot.reply_to(message, 'Очередь пуста.')
    else:
        bot.reply_to(message, f'Пользователь с id {user_id} удален из очереди.')

@bot.message_handler(commands=['size'])
def queue_size(message):
    size = user_queue.size()
    bot.reply_to(message, f'Размер очереди: {size}.')

@bot.message_handler(commands=['display'])
def display_queue(message):
    queue_message = user_queue.display_queue()
    bot.reply_to(message, queue_message)

@bot.message_handler(func=lambda message: message.text.lower() == 'получить заказ')
def remove_user_from_queue(message):
    user_id = message.from_user.first_name

    # Проверка, есть ли пользователь в очереди
    if user_id not in user_queue.queue:
        bot.reply_to(message, 'Вы не находитесь в очереди. Заказ недоступен.')
        return

    user_queue.remove_user(user_id)
    rl = generate_random_letters(50)
    print(rl)
    qrcode = make_qr(rl)
    qrcode.save("metanit_qr.png", dark="#2980B9", border=4, scale=5)
    file = open('./metanit_qr.png', 'rb')
    bot.send_photo(message.chat.id, file)
    bot.reply_to(message, 'Вы удалены из очереди.')

class CartItem:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        for existing_item in self.items:
            if existing_item.name == item.name:
                existing_item.quantity += item.quantity
                return
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)

    def clear_cart(self):
        self.items = []

    def get_total_price(self):
        total = 0
        for item in self.items:
            total += item.price * item.quantity
        return total

    def display_cart(self):
        cart_message = ''
        for item in self.items:
            cart_message += f'{item.name} - {item.quantity} шт., Цена: {item.price} руб.\n'
        cart_message += f'Итого: {self.get_total_price()} руб.'
        return cart_message

cart = Cart()

@bot.message_handler(commands=['Добавить'])
def add_item(message):
    item_name = message.text.split()[1]
    item_price = 0
    item_quantity = 1

    if item_name == 'борщ':
        item_price = 45
    elif item_name == 'биточки':
        item_price = 75
    elif item_name == 'пюрешочка':
        item_price = 20
    elif item_name == 'гречечка':
        item_price = 25
    elif item_name == 'эшпошмак':
        item_price = 34
    elif item_name == 'Чибуречек':
        item_price = 99999
    else:
        bot.reply_to(message, 'Такого товара нет в буфете.')
        return

    item = CartItem(item_name, item_price, item_quantity)
    cart.add_item(item)
    bot.reply_to(message, 'Товар успешно добавлен в корзину.')

@bot.message_handler(commands=['Цена'])
def display_cart(message):
    cart_message = cart.display_cart()
    bot.reply_to(message, cart_message)

@bot.message_handler(commands=['Отчистить'])
def clear_cart(message):
    cart.clear_cart()
    bot.reply_to(message, 'Корзина успешно очищена.')


def generate_random_letters(length):
    letters = string.ascii_letters
    random_letters = ''.join(random.choice(letters) for _ in range(length))
    return random_letters

#начало программы, школьник вводит свой уникальный индификатор, проверяемый на соответствие с базой данных
@bot.message_handler(commands=['start'])
def indification(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(''))
    bot.send_message(message.chat.id, 'Введите свой индификартор!')
    if message.text.lower() == 'doedo.inno':
        bot.send_message(message.chat.id, 'dfghjkl')

@bot.message_handler()
def info(message):
    if message.text in m:
        bot.send_message(message.chat.id, f'Добрый день, {message.from_user.first_name}')
        menu(message)
    elif message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Доброе утро, Андрей')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f"ID, {message.from_user.id}")
    elif message.text.lower() == 'хочу эчпочмак':
        webbrowser.open_new_tab(
            'https://www.google.com/search?q=%D1%85%D0%BE%D1%87%D1%83+%D1%8D%D1%87%D0%BF%D0%BE%D1%87%D0%BC%D0%B0%D0%BA&sca_esv=572890011&rlz=1C1GCEU_ruRU1029RU1029&tbm=isch&sxsrf=AM9HkKkoAsdWqYClJiNzYzYU2CubV8KHnw:1697130072329&source=lnms&sa=X&ved=2ahUKEwjk0eSY_vCBAxUyLRAIHSHwDYwQ_AUoAXoECAMQAw&biw=1536&bih=747&dpr=1.25#imgrc=_YfNV51Hmto2TM')
        file = open('./photo.jpg', 'rb')
        bot.send_photo(message.chat.id, file)
    elif message.text.lower() == 'меню':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        vibor(message)
        file = open('./menu_add.jpg', 'rb')
        bot.send_photo(message.chat.id, file)
    elif message.text.lower() == 'супы 🥘':
        for i in range(0,len(soup),2):
            bot.send_message(message.chat.id, soup[i])
    elif message.text.lower() == 'второе 🍛':
        for i in range(0,len(soup),2):
            bot.send_message(message.chat.id, basic[i])
    elif message.text.lower() == 'гарнир 🍚':
        for i in range(0,len(soup),2):
            bot.send_message(message.chat.id, garnish[i])
    elif message.text.lower() == 'напитки 🧋':
        for i in range(0,len(soup),2):
            bot.send_message(message.chat.id, drinks[i])
    elif message.text.lower() == 'изменить меню':
        if message.from_user.id == 829836737:
            pass
    elif message.text.lower() == 'получить заказ':
        rl = generate_random_letters(50)
        print(rl)
        qrcode = make_qr(rl)
        # цвет - #2980B9, граница - 4, масштабирование - в 5 раз
        qrcode.save("metanit_qr.png", dark="#2980B9", border=4, scale=5)
        file = open('./metanit_qr.png','rb')
        bot.send_photo(message.chat.id, file)
    elif message.text.lower() == 'назад':
        menu(message)
    elif message.text.lower() == 'корзина':
        korzina(message)
    elif message.text.lower() == 'электронная очередь':
        queue(message)




@bot.message_handler()
def vibor(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Супы 🥘')
    btn2 = types.KeyboardButton('Второе 🍛')
    markup.add(btn1,btn2)
    btn3 = types.KeyboardButton('Гарнир 🍚')
    btn4 = types.KeyboardButton('Напитки 🧋')
    btn5 = types.KeyboardButton('Назад')
    markup.add(btn3, btn4)
    markup.add(btn5)
    bot.send_message(message.chat.id, 'Вот сегодняшнее меню!', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Электронная очередь')
    markup.add(btn1)
    btn2 = types.KeyboardButton('Корзина')
    btn3 = types.KeyboardButton('Получить заказ')
    btn4 = types.KeyboardButton('Меню')
    markup.add(btn2, btn3)
    markup.add(btn4)
    bot.send_message(message.chat.id, 'Вот мой функционал!', reply_markup=markup)
@bot.message_handler()
def korzina(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/Добавить борщ 🍛')
    btn2 = types.KeyboardButton('/Добавить пюрешочка 🥧')
    markup.add(btn1,btn2)
    btn3 = types.KeyboardButton('/Добавить биточки 🧆')
    btn4 = types.KeyboardButton('/Добавить гречечка 🫘')
    markup.add(btn3,btn4)
    btn5 = types.KeyboardButton('/Добавить эшпошмак 🥠')
    btn6 = types.KeyboardButton('/Добавить Чибуречек 🥟')
    markup.add(btn5,btn6)
    btn7 = types.KeyboardButton('/Цена')
    btn8 = types.KeyboardButton('/Отчистить')
    markup.add(btn7,btn8)
    btn9 = types.KeyboardButton('Назад')
    markup.add(btn9)
    bot.send_message(message.chat.id, 'Вот что есть в ассортименте', reply_markup=markup)

@bot.message_handler()
def queue(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/enqueue')
    btn2 = types.KeyboardButton('/dequeue')
    markup.add(btn1, btn2)
    btn3 = types.KeyboardButton('/display')
    markup.add(btn3)
    btn4 = types.KeyboardButton('Назад')
    markup.add(btn4)
    bot.send_message(message.chat.id, 'Вот очередь', reply_markup=markup)


bot.infinity_polling()