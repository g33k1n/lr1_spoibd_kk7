import telebot
import threading
import random
import time

bot = telebot.TeleBot("8130581202:AAFb5xN-9DII429WUfSgSmPKMUXKsyA1Bog")  # Замените на токен вашего бота

# Словарь приветственных сообщений для команды /start
start_texts = {
    1: "Привет! Я учебный бот. Могу поделиться интересным фактом или задать тебе вопрос!Используй команды /fact и /quiz, чтобы узнать что-то новое.Или /game для игры. Так же есть команда /random_text",
    2: "Добро пожаловать! Используй команды /fact и /quiz, чтобы узнать что-то новое.Или /game для игры или команду /random_text",
    3: "Привет! Готов помочь тебе с учебой. Попробуй команды /fact, /quiz или /game /random_text"
}

# Список учебных фактов для команды /fact
facts = [
    "Планета Венера вращается в обратную сторону относительно Земли.",
    "Самая длинная река в мире — Нил.",
    "Человеческий мозг весит около 1.4 кг.",
    "Скорость света — 299 792 458 м/с.",
]
active_threads = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    random_text = random.choice(list(start_texts.values()))
    bot.reply_to(message, random_text)


@bot.message_handler(commands=['fact'])
def fact_message(message):
    random_fact = random.choice(facts)
    bot.reply_to(message, f"Вот интересный факт: {random_fact}")


@bot.message_handler(commands=['quiz'])
def quiz_message(message):
    bot.send_message(message.chat.id, "Вопрос: Какая планета самая горячая в нашей Солнечной системе?")

    def check_answer(msg):
        if msg.text.lower() == 'венера':
            bot.reply_to(msg, "Правильно! Венера — самая горячая.")
        else:
            bot.reply_to(msg, "Неправильно. Правильный ответ — Венера.")

    bot.register_next_step_handler(message, check_answer)


@bot.message_handler(commands=['random_text'])
def random_text_timer(message):
    chat_id = message.chat.id
    if chat_id in active_threads:
        bot.reply_to(message, "Отправка уже запущена. Чтобы остановить, используй команду /stop.")
        return

    bot.reply_to(message, "Буду отправлять случайные тексты каждую минуту. Чтобы остановить, напиши /stop.")

    # Функция для отправки случайного текста
    def send_text_periodically(chat_id, stop_event):
        while not stop_event.is_set():
            with open('texts.txt', 'r', encoding='utf-8') as file:
                lines = file.readlines()
            random_line = random.choice(lines).strip()
            bot.send_message(chat_id, random_line)
            stop_event.wait(60)  # Ждет 60 секунд или остановки

    # Создаем поток и событие для остановки
    stop_event = threading.Event()
    thread = threading.Thread(target=send_text_periodically, args=(chat_id, stop_event), daemon=True)
    active_threads[chat_id] = (thread, stop_event)
    thread.start()

@bot.message_handler(commands=['stop'])
def stop_random_text(message):
    chat_id = message.chat.id
    if chat_id in active_threads:
        # Устанавливаем флаг остановки и удаляем поток из словаря
        _, stop_event = active_threads.pop(chat_id)
        stop_event.set()
        bot.reply_to(message, "Отправка сообщений остановлена.")
    else:
        bot.reply_to(message, "Сейчас ничего не отправляется.")

@bot.message_handler(commands=['game'])
def start_game(message):
    bot.send_message(message.chat.id, "Начнем игру! Я буду задавать примеры на сложение. Для завершения напиши 'стоп'.")

    def ask_question(msg):
        # Проверка, если пользователь ввел "стоп"
        if msg.text.lower() == 'стоп':
            bot.send_message(msg.chat.id, "Игра завершена. Спасибо за участие!")
            return

        # Генерация примера на сложение
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        correct_answer = num1 + num2
        bot.send_message(msg.chat.id, f"Сколько будет {num1} + {num2}?")

        # Вложенная функция для проверки ответа
        def check_answer(response):
            if response.text.lower() == 'стоп':
                bot.send_message(response.chat.id, "Игра завершена. Спасибо за участие!")
                return
            try:
                if int(response.text) == correct_answer:
                    bot.send_message(response.chat.id, "Молодец! Правильный ответ.")
                else:
                    bot.send_message(response.chat.id, f"Неправильно. Правильный ответ был {correct_answer}.")
            except ValueError:
                bot.send_message(response.chat.id, "Пожалуйста, введи число или 'стоп' для завершения.")

            # Задаем новый вопрос или завершаем, если 'стоп'
            ask_question(response)

        bot.register_next_step_handler(msg, check_answer)

    ask_question(message)


bot.polling(none_stop=True)
