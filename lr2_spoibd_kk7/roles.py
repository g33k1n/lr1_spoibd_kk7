import sqlite3
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import telebot

API_TOKEN = '8130581202:AAFb5xN-9DII429WUfSgSmPKMUXKsyA1Bog'

bot = telebot.TeleBot(API_TOKEN)

ROLE_MANAGER = 'manager'
ROLE_DIRECTOR = 'director'


class MessageStats:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect_db(self):
        return sqlite3.connect(self.db_path)

    def get_messages(self, start_date=None, end_date=None):
        with self.connect_db() as conn:
            cursor = conn.cursor()
            query = "SELECT user_id, message, command, timestamp FROM messages"
            params = []

            if start_date and end_date:
                query += " WHERE timestamp BETWEEN ? AND ?"
                start_ts = datetime.strptime(start_date, '%Y-%m-%d').timestamp()
                end_ts = datetime.strptime(end_date, '%Y-%m-%d').timestamp()
                params.extend([start_ts, end_ts])

            cursor.execute(query, params)
            return cursor.fetchall()

    def process_stats(self, start_date=None, end_date=None):
        messages = self.get_messages(start_date, end_date)
        daily_stats = defaultdict(int)
        user_stats = defaultdict(int)
        command_stats = defaultdict(int)

        for user_id, message, command, timestamp in messages:
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            daily_stats[date] += 1
            user_stats[user_id] += 1
            if command:
                command_stats[command] += 1

        return {
            'daily_stats': dict(daily_stats),
            'user_stats': dict(user_stats),
            'command_stats': dict(command_stats)
        }

    def display_stats(self, start_date=None, end_date=None):
        stats = self.process_stats(start_date, end_date)
        df = pd.DataFrame.from_dict(stats['daily_stats'], orient='index', columns=['Messages'])
        df.index.name = 'Date'
        print(df)

        df.plot(kind='bar', figsize=(10, 6), title=f'Daily Message Statistics ({start_date} to {end_date})')
        plt.ylabel('Messages')
        plt.xlabel('Date')
        plt.tight_layout()
        plt.savefig('daily_stats.png')
        plt.show()


# Управление авторизацией и ролями пользователей
users_roles = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать!")


@bot.message_handler(commands=['grant_manager'])
def grant_manager(message):
    if message.from_user.id in users_roles and users_roles[message.from_user.id] == ROLE_DIRECTOR:
        parts = message.text.split()
        if len(parts) > 1:
            target_id = int(parts[1])
            users_roles[target_id] = ROLE_MANAGER
            bot.send_message(message.chat.id, f"Пользователь {target_id} назначен Управляющим.")
        else:
            bot.send_message(message.chat.id, "Укажите ID пользователя.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.message_handler(commands=['grant_director'])
def grant_director(message):
    if message.from_user.id in users_roles and users_roles[message.from_user.id] == ROLE_DIRECTOR:
        parts = message.text.split()
        if len(parts) > 1:
            target_id = int(parts[1])
            users_roles[target_id] = ROLE_DIRECTOR
            bot.send_message(message.chat.id, f"Пользователь {target_id} назначен Руководителем.")
        else:
            bot.send_message(message.chat.id, "Укажите ID пользователя.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    if user_id in users_roles and users_roles[user_id] in [ROLE_DIRECTOR]:
        parts = message.text.split()
        if len(parts) == 3:
            start_date = parts[1]
            end_date = parts[2]
        else:
            start_date = None
            end_date = None

        stats = MessageStats("bot_messages.db")
        stats.display_stats(start_date, end_date)
        with open('daily_stats.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Статистика с {start_date} по {end_date}.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для просмотра статистики.")


@bot.message_handler(commands=['edit_response'])
def edit_response(message):
    user_id = message.from_user.id
    if user_id in users_roles and users_roles[user_id] in [ROLE_MANAGER, ROLE_DIRECTOR]:
        bot.send_message(message.chat.id, "Вы можете редактировать ответы бота.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для редактирования ответов.")


if __name__ == "__main__":
    bot.polling(none_stop=True)