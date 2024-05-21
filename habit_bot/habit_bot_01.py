import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
import psycopg2
import datetime
from telegram.ext import ConversationHandler
from tabulate import tabulate

# Инициализация логгера
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(database="habit", user="postgres", password="postgres", host="localhost", port="5432")
cursor = conn.cursor()

# Создание таблицы для хранения привычек в базе данных
cursor.execute('CREATE TABLE IF NOT EXISTS user_habits (user_id INTEGER, habit TEXT, activation_date DATE);')
conn.commit()

# Создание таблицы для хранения выполненных привычек в базе данных
cursor.execute('CREATE TABLE IF NOT EXISTS habit_checkmarks (user_id INTEGER, habit TEXT, check_date DATE);')
conn.commit()

# Обработчик команды /start
def start(update: Update, context) -> None:
    update.message.reply_text('Привет! Я помогу тебе следить за выполнением твоих целей и привычек.')

# Функция для добавления привычки в базу данных
def add_habit(update: Update, context) -> None:
    context.chat_data['awaiting_habit'] = True
    context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, введите название привычки.')

# Функция для отображения привычек из базы данных
def show_habits(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id

    cursor.execute('SELECT habit FROM user_habits WHERE user_id=%s', (user_id,))
    habits = cursor.fetchall()

    if not habits:
        context.bot.send_message(chat_id=update.effective_chat.id, text='У вас пока нет добавленных привычек.')
    else:
        keyboard = []
        for habit in habits:
            cursor.execute('SELECT COUNT(*) FROM habit_checkmarks WHERE user_id=%s AND habit=%s AND check_date=%s', (user_id, habit[0], datetime.date.today()))
            count = cursor.fetchone()[0]
            status = " (выполнено)" if count > 0 else " (не выполнено)"
            keyboard.append([InlineKeyboardButton(f"{habit[0]}{status}", callback_data=f"uncheck_{habit[0]}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите привычку для отметки выполнения:", reply_markup=reply_markup)


def check_uncheck_habit(update: Update, context: CallbackContext) -> None:
    habit = update.callback_query.data.split('_')[1]
    user_id = update.effective_chat.id

    cursor.execute('SELECT COUNT(*) FROM habit_checkmarks WHERE user_id=%s AND habit=%s AND check_date=%s', (user_id, habit, datetime.date.today()))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute('DELETE FROM habit_checkmarks WHERE user_id=%s AND habit=%s AND check_date=%s', (user_id, habit, datetime.date.today()))
        conn.commit()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" отменена.')
    else:
        cursor.execute('INSERT INTO habit_checkmarks (user_id, habit, check_date) VALUES (%s, %s, %s)', (user_id, habit, datetime.date.today()))
        conn.commit()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" выполнена.')

    logger.info(f'Привычка "{habit}" выполнена/отменена пользователем с ID {user_id}')

def handle_habit_input(update: Update, context: CallbackContext) -> None:
    if 'awaiting_habit' in context.chat_data and context.chat_data['awaiting_habit']:
        habit = update.message.text
        user_id = update.effective_chat.id

        cursor.execute('SELECT * FROM user_habits WHERE user_id=%s AND habit=%s', (user_id, habit))
        existing_habit = cursor.fetchone()

        if existing_habit:
            # Запрос подтверждения удаления
            context.chat_data['confirming_deletion'] = True
            context.chat_data['habit_to_delete'] = habit
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" уже существует. Вы уверены, что хотите её удалить? Введите "да" или "нет".')
        else:
            cursor.execute('INSERT INTO user_habits (user_id, habit) VALUES (%s, %s)', (user_id, habit))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit}" добавлена.')

        context.chat_data['awaiting_habit'] = False
    elif 'confirming_deletion' in context.chat_data and context.chat_data['confirming_deletion']:
        habit_to_delete = context.chat_data["habit_to_delete"]
        user_id = update.effective_chat.id
        text = update.message.text.lower()

        if text == "да":
            # Удаляем привычку
            cursor.execute('DELETE FROM user_habits WHERE user_id=%s AND habit=%s', (user_id, habit_to_delete))
            cursor.execute('DELETE FROM habit_checkmarks WHERE user_id=%s AND habit=%s', (user_id, habit_to_delete))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Привычка "{habit_to_delete}" удалена.')
        elif text == "нет":
            context.bot.send_message(chat_id=update.effective_chat.id, text='Удаление привычки отменено.')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, введите "да" или "нет". Вы ввели неправильную команду.')
            return

        context.chat_data['awaiting_habit'] = False
        context.chat_data['confirming_deletion'] = False
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Пожалуйста, введите название привычки после команды.')

def habit_handler(update, context):
    query = update.callback_query
    if query.data.startswith("check_"):
        check_habit(update, context)

def show_weekly_stats(update: Update, context: CallbackContext) -> None: 
    user_id = update.effective_chat.id 
    current_date = datetime.date.today()

    start_date = current_date - datetime.timedelta(days=current_date.weekday())
    end_date = start_date + datetime.timedelta(days=6)

    cursor.execute('SELECT habit, COUNT(*) FROM habit_checkmarks WHERE user_id=%s AND check_date BETWEEN %s AND %s GROUP BY habit', (user_id, start_date, end_date))
    weekly_stats = cursor.fetchall()

    habits_stats = {}
    for habit, count in weekly_stats:
        habits_stats[habit] = count

    sorted_habits = sorted(habits_stats.items(), key=lambda x: x[1], reverse=True)

    data = []
    response = f"Сводка за неделю {start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}:\n"
    for habit, count in sorted_habits:
        cursor.execute('SELECT COUNT(check_date) FROM habit_checkmarks WHERE user_id=%s AND habit=%s AND check_date BETWEEN %s AND %s', (user_id, habit, start_date, end_date))
        max_series = cursor.fetchone()[0]

        data.append([habit, f"{count} раз", f"{max_series} дня подряд"])

    headers = [" Название ", "Всего", "Серия"]
    weekly_summary = f"Сводка за неделю\n{start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')}\n"
    
    response = weekly_summary + "```\n" + tabulate(data, headers, tablefmt="plain", numalign="right", stralign="center") + "\n```"
    response = response.replace("-", "\-")  # Escape the '-' character

    context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="MarkdownV2")

def show_monthly_stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id
    current_date = datetime.date.today()

    month_start_date = current_date.replace(day=1)
    month_end_date = month_start_date.replace(month=month_start_date.month % 12 + 1) - datetime.timedelta(days=1)

    cursor.execute('SELECT habit, COUNT(*) FROM habit_checkmarks WHERE user_id=%s AND check_date BETWEEN %s AND %s GROUP BY habit', (user_id, month_start_date, month_end_date))
    monthly_stats = cursor.fetchall()

    habits_stats = {}
    for habit, count in monthly_stats:
        habits_stats[habit] = count

    sorted_habits = sorted(habits_stats.items(), key=lambda x: x[1], reverse=True)

    data = []
    for habit, count in sorted_habits:
        cursor.execute('SELECT COUNT(check_date) FROM habit_checkmarks WHERE user_id=%s AND habit=%s AND check_date BETWEEN %s AND %s', (user_id, habit, month_start_date, month_end_date))
        max_series = cursor.fetchone()[0]

        data.append([habit, f"{count} раз", f"{max_series} дня подряд"])

    headers = [" Название ", "Всего", "Серия"]
    month_summary = f"Сводка за месяц\n{month_start_date.strftime('%d-%m-%Y')} - {month_end_date.strftime('%d-%m-%Y')}\n"
    
    response = month_summary + "```\n" + tabulate(data, headers, tablefmt="plain", numalign="right", stralign="center") + "\n```"
    response = response.replace("-", "\-")  # Escape the '-' character

    context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="MarkdownV2")

def show_total_stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id

    cursor.execute('SELECT habit, COUNT(*) FROM habit_checkmarks WHERE user_id=%s GROUP BY habit', (user_id,))
    total_stats = cursor.fetchall()

    habits_stats = {}
    for habit, count in total_stats:
        habits_stats[habit] = count

    sorted_habits = sorted(habits_stats.items(), key=lambda x: x[1], reverse=True)

    data = []
    for habit, count in sorted_habits:
        cursor.execute('SELECT COUNT(check_date) FROM habit_checkmarks WHERE user_id=%s AND habit=%s', (user_id, habit))
        max_series = cursor.fetchone()[0]

        data.append([habit, f"{count} раз", f"{max_series} дня подряд"])

    headers = [" Название ", "Всего", "Серия"]
    total_summary = "Сводка за весь период"
    
    response = total_summary + "```\n" + tabulate(data, headers, tablefmt="plain", numalign="right", stralign="center") + "\n```"
    response = response.replace("-", "\-")  # Escape the '-' character

    context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="MarkdownV2")


def main() -> None:
    updater = Updater("6613496794:AAHDt-diAM6JS9ET244SMxMBicWSCxK_z1s")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("addhabit", add_habit))
    dispatcher.add_handler(CallbackQueryHandler(habit_handler, pattern="check_.*|uncheck_.*"))
    dispatcher.add_handler(CommandHandler("habits", show_habits))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_habit_input))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("weeklystats", show_weekly_stats))
    dispatcher.add_handler(CommandHandler("monthlystats", show_monthly_stats))
    dispatcher.add_handler(CommandHandler("totalstats", show_total_stats))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()