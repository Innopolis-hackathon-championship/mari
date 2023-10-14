# menu_handler.py
from telebot import types

def handle_korzina(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/Добавить борщ 🍛')
    btn2 = types.KeyboardButton('/Добавить пюрешочка 🥧')
    markup.add(btn1, btn2)
    btn3 = types.KeyboardButton('/Добавить биточки 🧆')
    btn4 = types.KeyboardButton('/Добавить гречечка 🫘')
    markup.add(btn3, btn4)
    btn5 = types.KeyboardButton('/Добавить эшпошмак 🥠')
    btn6 = types.KeyboardButton('/Добавить Чибуречек 🥟')
    markup.add(btn5, btn6)
    btn7 = types.KeyboardButton('/Цена')
    btn8 = types.KeyboardButton('/Отчистить')
    markup.add(btn7, btn8)
    btn10 = types.KeyboardButton('Назад')
    markup.add(btn10)
    bot.send_message(message.chat.id, 'Вот что есть в ассортименте', reply_markup=markup)