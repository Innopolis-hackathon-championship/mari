import telebot
from datetime import datetime, timedelta
from telebot import types
from telebot.apihelper import ApiException

from config import Config

bot = telebot.TeleBot(token=Config.token)

# Словарь для отслеживания времени последнего сообщения от каждого пользователя
last_message_time = {}

TIMEOUT_SECONDS = 5

def throttling_middleware(message):
    global last_message_time

    user_id = message.from_user.id
    current_time = datetime.now()

    if user_id in last_message_time:
        elapsed_time = current_time - last_message_time[user_id]
        if elapsed_time.total_seconds() < TIMEOUT_SECONDS:
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except ApiException as e:
                print(f"Error deleting message: {e}")
            return

    last_message_time[user_id] = current_time

    return message