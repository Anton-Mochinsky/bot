# import telebot
# import psycopg2
# from telebot import types
# import bcrypt

# bot = telebot.TeleBot('6969253112:AAHds4w2mxWlZQTUsTUSlX3LTHfA8UFdLwA')
# conn = psycopg2.connect(
#     dbname="fitnes",
#     user="postgres",
#     password="postgres",
#     host="localhost",
#     port="5432"
# )
# cursor = conn.cursor()

# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id SERIAL PRIMARY KEY,
#         user_id INTEGER UNIQUE,
#         username VARCHAR(255),
#         password TEXT
#     )
# """)


# # Регистрация пользователя
# @bot.message_handler(commands=['register'])
# def register(message):
#     username = message.from_user.first_name
#     bot.send_message(message.chat.id, "Для завершения регистрации, введите пароль:")
#     bot.register_next_step_handler(message, lambda message: save_password(message, username))

# def save_password(message, username):
#     password = message.text
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

#     cursor.execute("INSERT INTO users (user_id, username, password) VALUES (%s, %s, %s)", (message.chat.id, username, hashed_password))
#     conn.commit()

#     bot.send_message(message.chat.id, "Регистрация прошла успешно. Для выхода введите /logout.")

# # Стартовое сообщение
# @bot.message_handler(commands=['start'])
# def start(message):
#     cursor.execute("SELECT * FROM users WHERE id=%s", (message.chat.id,))
#     user = cursor.fetchone()
#     if user:
#         markup = types.ReplyKeyboardMarkup(row_width=2)
#         buttons = ["Получить программу тренировок", "Получить рекомендации по питанию", "Мотивационная цитата"]

#         for button in buttons:
#             markup.add(types.KeyboardButton(button))

#         bot.send_message(message.chat.id, f"Привет, {user[1]}! Чем могу помочь?", reply_markup=markup)
#     else:
#         bot.send_message(message.chat.id, "Для начала вам необходимо зарегистрироваться. Введите ваше имя:")
#         bot.register_next_step_handler(message, register)

# @bot.message_handler(commands=['login'])
# def login(message):
#     bot.send_message(message.chat.id, "Введите ваше имя пользователя:")
#     bot.register_next_step_handler(message, check_username)

# def check_username(message):
#     username = message.text
#     bot.send_message(message.chat.id, "Введите ваш пароль:")
#     bot.register_next_step_handler(message, lambda message: check_password(message, username))

# def check_password(message, username):
#     password = message.text
#     cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
#     user = cursor.fetchone()
    
#     if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
#         bot.send_message(message.chat.id, f"Добро пожаловать, {username}! Чем могу помочь?")
#     else:
#         bot.send_message(message.chat.id, f"Неправильное имя пользователя или пароль. Попробуйте снова.")

# # Обработка запросов пользователя
# @bot.message_handler(func=lambda message: True)
# def handle_message(message):
#     cursor.execute("SELECT * FROM users WHERE id=%s", (message.chat.id,))
#     user = cursor.fetchone()
    
#     if not user:
#         bot.send_message(message.chat.id, "Для начала вам необходимо зарегистрироваться или войти. Используйте /register или /login.")
#     else:
#         command = message.text
#         if command == "Получить программу тренировок":
#             bot.send_message(message.chat.id, "Ваша программа тренировок: ...")
#         elif command == "Получить рекомендации по питанию":
#             bot.send_message(message.chat.id, "Ваши рекомендации по питанию: ...")
#         elif command == "Мотивационная цитата":
#             bot.send_message(message.chat.id, "Мотивационная цитата: ...")
#         else:
#             bot.send_message(message.chat.id, "Извините, я не понимаю ваш запрос. Пожалуйста, используйте кнопки меню.")

# # Выход из аккаунта
# @bot.message_handler(commands=['logout'])
# def logout(message):
#     cursor.execute("DELETE FROM users WHERE user_id=%s", (message.chat.id,))
#     conn.commit()
#     bot.send_message(message.chat.id, "Вы успешно вышли из аккаунта.")

# # Запуск бота
# bot.polling()



# import logging
# from telegram import Update, Bot
# from telegram.ext import Updater, CommandHandler, CallbackContext
# import psycopg2
# import datetime
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# # Инициализация логгера
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Подключение к базе данных PostgreSQL
# conn = psycopg2.connect(database="habit", user="postgres", password="postgres", host="localhost", port="5432")
# cursor = conn.cursor()

# # Создание таблицы для хранения привычек в базе данных
# cursor.execute('CREATE TABLE IF NOT EXISTS user_habits (user_id INTEGER, habit TEXT)')
# conn.commit()

# # Обработчик команды /start
# def start(update: Update, context) -> None:
#     update.message.reply_text('Привет! Я помогу тебе следить за выполнением твоих целей и привычек.')

#     # Создание кнопки "Меню"
#     keyboard = [[InlineKeyboardButton("Меню", callback_data='menu')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     update.message.reply_text('Чтобы открыть меню, нажмите кнопку ниже:', reply_markup=reply_markup)

# # Функция для добавления привычки в базу данных
# def add_habit(update: Update, context) -> None:
#     habit = ' '.join(context.args)
#     user_id = update.effective_chat.id

#     if habit:
#         cursor.execute('INSERT INTO user_habits (user_id, habit) VALUES (%s, %s)', (user_id, habit))
#         conn.commit()
#         context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" добавлена.')
#     else:
#         context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, укажите название привычки после команды.')

# # Функция для удаления привычки из базы данных
# def remove_habit(update: Update, context) -> None:
#     habit = ' '.join(context.args)
#     user_id = update.effective_chat.id

#     if habit:
#         cursor.execute('DELETE FROM user_habits WHERE user_id=%s AND habit=%s', (user_id, habit))
#         conn.commit()
#         context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" удалена.')
#     else:
#         context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, укажите название привычки после команды.')

# # Функция для отображения привычек из базы данных
# def show_habits(update: Update, context) -> None:
#     user_id = update.effective_chat.id

#     cursor.execute('SELECT habit FROM user_habits WHERE user_id=%s', (user_id,))
#     habits = cursor.fetchall()

#     if not habits:
#         context.bot.send_message(chat_id=update.effective_chat.id, text='У вас пока нет добавленных привычек.')
#     else:
#         habits_list = "\n".join([f'Привычка "{habit[0]}"' for habit in habits])
#         context.bot.send_message(chat_id=update.effective_chat.id, text=f'Ваши привычки:\n{habits_list}')

# # Callback функция для обработки нажатий на inline кнопки
# def button_click(update, context):
#     query = update.callback_query
#     command = query.data

#     if command == 'menu':
#         menu(update, context)
#     else:
#         query.message.reply_text(f'Выбрана команда: {command}')

# def main() -> None:
#     updater = Updater("6613496794:AAHDt-diAM6JS9ET244SMxMBicWSCxK_z1s")

#     dispatcher = updater.dispatcher
    
#     dispatcher.add_handler(CommandHandler("start", start))
#     dispatcher.add_handler(CommandHandler("addhabit", add_habit))
#     dispatcher.add_handler(CommandHandler("removehabit", remove_habit))
#     dispatcher.add_handler(CommandHandler("habits", show_habits))
#     dispatcher.add_handler(CommandHandler("menu", menu))
#     dispatcher.add_handler(CommandHandler('callback', button_click))

#     updater.start_polling()
#     updater.idle()


# def menu(update: Update, context) -> None:
#     # Определение содержимого меню
#     menu_text = "Меню:\n"
#     menu_text += "/addhabit - добавить привычку"
#     menu_text += "/removehabit - удалить привычку"
#     menu_text += "/habits - показать привычки"

#     update.message.reply_text(menu_text)


# if __name__ == '__main__':
#     main()