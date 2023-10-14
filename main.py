import telebot
from telebot import types
from segno import*

import random
import sqlite3

import webbrowser
import string

from pyzbar.pyzbar import decode
import cv2

import numpy as np
indificator = None

from keyboards.korzina_def import handle_korzina
from config import Config
from middlewares.throtting import throttling_middleware


mika = []
follow = {}


#индификаторы
m = ["doedo.inno", "edjfi.inno", "feodo.inno"]
admin_id = admin_id=Config.admin_id
bot = telebot.TeleBot(token=Config.token)
indif = None

# Список ассортимента
assortment = {
    'борщ': 45,
    'биточки': 75,
    'пюрешочка': 20,
    'гречечка': 25,
    'эшпошмак': 34,
    'Чибуречек': 65,
}
@bot.message_handler(commands=['Оплатить'])
def handle_payment(message):
    payment_button = types.InlineKeyboardButton("Оплатить заказ", callback_data='payment')
    keyboard = types.InlineKeyboardMarkup().add(payment_button)
    bot.send_message(message.chat.id, 'Нажмите на кнопку для оплаты заказа:', reply_markup=keyboard)

# ...

@bot.callback_query_handler(func=lambda call: call.data == 'payment')
def process_payment(callback_query):
    # Здесь вы можете добавить логику обработки оплаты
    # Например, отправка инструкций по оплате, ссылки на платежный сервис и т.д.
    bot.send_message(callback_query.from_user.id, 'Процесс оплаты...')
    bot.send_message(callback_query.from_user.id, 'Оплата успешно совершена')
# Функция для изменения ассортимента
def update_assortment(item_name, item_price):
    assortment[item_name] = item_price

@bot.message_handler(func=lambda message: message.text.lower() == 'изменить ассортимент')
def change_assortment(message):
    if message.from_user.id == admin_id:  # Проверка на администратора (ваш ID)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for item_name, item_price in assortment.items():
            markup.add(types.KeyboardButton(f'/Изменить {item_name} {item_price}'))

        btn_back = types.KeyboardButton('Назад')
        markup.add(btn_back)

        bot.send_message(message.chat.id, 'Выберите товар для изменения:', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'У вас нет прав для изменения ассортимента.')

@bot.message_handler(func=lambda message: message.text.startswith('/Изменить'))
def handle_change_assortment(message):
    if message.from_user.id == admin_id:  # Проверка на администратора (ваш ID)
        try:
            _, item_name, item_price = message.text.split()
            item_price = int(item_price)

            # Изменяем ассортимент
            update_assortment(item_name, item_price)

            bot.reply_to(message, f'Ассортимент обновлен: {item_name} - {item_price} руб.')

        except ValueError:
            bot.reply_to(message, 'Неверный формат команды. Используйте /Изменить <название> <цена>.')

    else:
        bot.send_message(message.chat.id, 'У вас нет прав для изменения ассортимента.')


#управление очередью
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

    def display_queue(self): #только для курьероов
        if self.is_empty():
            return "Очередь пуста."
        queue_message = "Текущая очередь:\n"
        for idx, user_id in enumerate(self.queue, start=1):
            queue_message += f'{idx}. {user_id}\n'
        return queue_message

    def remove_user(self, user_id):
        if user_id in self.queue:
            self.queue.remove(user_id)


user_queue = UserQueue()


#Заказ
@bot.message_handler(commands=['Заказ'])
def enqueue_user(message):
    user_id = message.from_user.first_name

    # Проверяем, заполнена ли корзина пользователя
    if not cart.items:
        bot.reply_to(message, 'Чтобы встать в очередь, сначала добавьте товары в корзину.')
        return

    user_queue.enqueue(user_id)
    bot.reply_to(message, f'Вы добавлены в очередь.')
    user_queue.notify_first_user()
@bot.message_handler(commands=['Выйти'])
def dequeue_user(message):
    user_id = user_queue.dequeue()
    if user_id is None:
        bot.reply_to(message, 'Очередь пуста.')
    else:
        bot.reply_to(message, f'Пользователь с id {user_id} удален из очереди.')


@bot.message_handler(commands=['Просмотр'])
def display_queue(message):
    queue_message = user_queue.display_queue()
    bot.reply_to(message, queue_message)

@bot.message_handler(func=lambda message: message.text.lower() == 'получить заказ')
def remove_user_from_queue(message):
    user_id = message.from_user.first_name

    # Проверка, есть ли пользователь в очереди
    if user_id not in user_queue.queue:
        bot.reply_to(message, 'Ваш qr сгенерирован, либо вы уже получили заказ.')
        return

    rl = generate_random_letters(50)
    print(rl)
    qrcode = make_qr(rl)
    qrcode.save("metanit_qr.png", dark="#2980B9", border=4, scale=5)
    file = open('../DataBase_test/metanit_qr.png', 'rb')
    bot.send_photo(message.chat.id, file)
    bot.reply_to(message, 'Получите свой заказ по QR коду.')
    user_queue.remove_user(user_id)
    receiving_order(message)


#Получение заказа и отзывы
@bot.message_handler(commands=['Получил'])
def handle_received(message):
    user_id = message.from_user.id

    bot.reply_to(message, 'Напишите свой отзыв и мы учтем ваше мнение в будущем.')

    bot.register_next_step_handler(message, handle_review)

def handle_review(message):
    user_id = message.from_user.id
    review = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 6):
        markup.add(types.KeyboardButton(str(i)))
    bot.send_message(user_id, 'Как вы оцениваете наш сервис?', reply_markup=markup)

    bot.register_next_step_handler(message, handle_rating, review)

def handle_rating(message, review):
    user_id = message.from_user.id
    rating = message.text

    try:
        # Сохраняем оценку в списке follow
        follow[user_id] = int(rating)

        # Добавляем отзыв и оценку в список mika
        mika.append({'user_id': user_id, 'review': review, 'rating': int(rating)})

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(user_id, 'Спасибо за ваш отзыв и оценку! Мы учтем ваше мнение в будущем.', reply_markup=markup)

        bot.register_next_step_handler(message)

    except ValueError:
        bot.send_message(user_id, 'Пожалуйста, введите цифру от 1 до 5.')



#Отзывы
@bot.message_handler(commands=['Отзывы'])
def show_reviews(message):
    user_id = message.from_user.id

    if not mika:
        bot.reply_to(message, 'Отзывов пока нет.')
        return

    # Вычисляем среднюю оценку
    average_rating = sum(review['rating'] for review in mika) / len(mika)

    # Формируем текст отзывов
    reviews_text = '\n\n'.join([f"{review['user_id']}: {review['review']} (Оценка: {review['rating']})" for review in mika])

    # Добавляем среднюю оценку к тексту отзывов
    reviews_text_with_rating = f'Отзывы:\n\n{reviews_text}\n\nСредняя оценка: {average_rating:.2f}'

    bot.send_message(user_id, reviews_text_with_rating)


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
        item_price = assortment['борщ']
    elif item_name == 'биточки':
        item_price = assortment['биточки']
    elif item_name == 'пюрешочка':
        item_price = assortment['пюрешочка']
    elif item_name == 'гречечка':
        item_price = assortment['гречечка']
    elif item_name == 'эшпошмак':
        item_price = assortment['эшпошмак']
    elif item_name == 'чибуречек':
        item_price = assortment['чибуречек']
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

@bot.message_handler(commands=['Очистить'])
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
    elif message.text.lower() == 'корзина':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        vibor(message)
    elif message.text.lower() == 'получить заказ':
        rl = generate_random_letters(50)
        print(rl)
        qrcode = make_qr(rl)
        # цвет - #2980B9, граница - 4, масштабирование - в 5 раз
        qrcode.save("metanit_qr.png", dark="#2980B9", border=4, scale=5)
        file = open('../DataBase_test/metanit_qr.png','rb')
        bot.send_photo(message.chat.id, file)
    elif message.text.lower() == 'назад':
        menu(message)
    elif message.text.lower() == 'меню':
        korzina(message)
    elif message.text.lower() == 'электронная очередь':
        queue(message)




@bot.message_handler()
def vibor(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/Цена 📃')
    btn2 = types.KeyboardButton('/Заказ 📒')
    btn4 = types.KeyboardButton('/Оплата 💷')
    btn3 = types.KeyboardButton('Назад')

    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn4)
    markup.add(btn3)

    bot.send_message(message.chat.id, 'Вот сегодняшнее меню!', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Электронная очередь')
    btn6 = types.KeyboardButton('Изменить ассортимент')
    if message.from_user.id == admin_id:
        markup.add(btn1)
        markup.add(btn6)
    btn2 = types.KeyboardButton('Корзина')
    btn3 = types.KeyboardButton('Получить заказ')
    btn4 = types.KeyboardButton('Меню')
    btn5 = types.KeyboardButton('/Отзывы 🗓')
    markup.add(btn2, btn3)
    markup.add(btn4)
    markup.add(btn5)
    bot.send_message(message.chat.id, 'Вот мой функционал!', reply_markup=markup)
    print(admin_id)

#Функция корзины
def korzina(message):
    handle_korzina(bot, message)

#функция очереди
@bot.message_handler()
def queue(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/Встать ⬆')
    btn3 = types.KeyboardButton('/Просмотр ⏱')
    markup.add(btn3)
    btn4 = types.KeyboardButton('Назад')
    markup.add(btn4)
    bot.send_message(message.chat.id, 'Вот очередь', reply_markup=markup)

#распознование QR кода
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id == admin_id:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)


            image_np = np.frombuffer(downloaded_file, np.uint8)
            image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            barcodes = decode(gray)

            for barcode in barcodes:
                data = barcode.data.decode('utf-8')
                bot.reply_to(message, f'QR Code содержит: {data}')


        except Exception as e:
            bot.reply_to(message, f'QR код не распознан: {str(e)}')

@bot.message_handler()
def receiving_order(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/Получил')
    markup.add(btn1)
    bot.send_message(message.chat.id, 'Подтвердите получение заказа', reply_markup=markup)
# Функция для обработки команды /получил






bot.infinity_polling()