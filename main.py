import telebot
from telebot import types
from datetime import datetime, timedelta
import time

TOKEN = '7010295317:AAHjyrAFkvqVMOrwo3EGfbCI_nlyPDuczuY'
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения данных о событиях {chat_id: [{name: str, times: list, days: list}]}
events = {}

# Статусы для отслеживания этапов ввода данных
user_data = {}

# Соответствие дней недели на русском и английском
days_mapping = {
    "Понедельник": "Monday",
    "Вторник": "Tuesday",
    "Среда": "Wednesday",
    "Четверг": "Thursday",
    "Пятница": "Friday",
    "Суббота": "Saturday",
    "Воскресенье": "Sunday"
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот-планировщик. Давайте создадим новое событие.")
    bot.send_message(message.chat.id, "Введите название события:")
    user_data[message.chat.id] = {'step': 'name', 'name': '', 'times': [], 'days': []}


@bot.message_handler(func=lambda message: True)
def event_handler(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала.")
        return

    if user_data[chat_id]['step'] == 'name':
        user_data[chat_id]['name'] = message.text
        user_data[chat_id]['step'] = 'time'
        bot.send_message(chat_id, "Введите время запуска события (в формате HH:MM). Введите 'Завершить', когда закончите.")

    elif user_data[chat_id]['step'] == 'time':
        if message.text.lower() == 'завершить':
            user_data[chat_id]['step'] = 'days'
            show_days_selection(chat_id)
        else:
            time_str = message.text
            try:
                datetime.strptime(time_str, "%H:%M")
                user_data[chat_id]['times'].append(time_str)
                bot.send_message(chat_id, f"Время '{time_str}' добавлено. Введите еще одно время или 'Завершить'.")
            except ValueError:
                bot.send_message(chat_id, "Некорректный формат времени. Пожалуйста, введите время в формате HH:MM.")


def show_days_selection(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    buttons = [types.InlineKeyboardButton(day, callback_data=day) for day in days]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("Завершить", callback_data="Завершить"))
    bot.send_message(chat_id, "Выберите дни недели для события (нажмите 'Завершить' для завершения):", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "Завершить":
        if user_data[chat_id]['days']:
            add_event(chat_id)
            bot.send_message(chat_id, "Ваше событие было запланировано!")
            show_events(chat_id)
        else:
            bot.send_message(chat_id, "Вы не выбрали ни одного дня. Пожалуйста, выберите хотя бы один день.")
            show_days_selection(chat_id)
    else:
        if call.data not in user_data[chat_id]['days']:
            user_data[chat_id]['days'].append(call.data)
            bot.answer_callback_query(call.id, f"{call.data} добавлен в список дней.")
        else:
            bot.answer_callback_query(call.id, f"{call.data} уже выбран.")


def add_event(chat_id):
    event = {
        'name': user_data[chat_id]['name'],
        'times': user_data[chat_id]['times'],
        'days': [days_mapping[day] for day in user_data[chat_id]['days']]
    }
    if chat_id in events:
        events[chat_id].append(event)
    else:
        events[chat_id] = [event]
    del user_data[chat_id]


def show_events(chat_id):
    if chat_id in events and events[chat_id]:
        event_list = "Запланированные события:\n"
        for idx, event in enumerate(events[chat_id], 1):
            event_list += f"{idx}. {event['name']} - Время: {', '.join(event['times'])} - Дни: {', '.join(event['days'])}\n"
        bot.send_message(chat_id, event_list)
    else:
        bot.send_message(chat_id, "У вас нет запланированных событий.")


def event_notification():
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")
        for chat_id, user_events in events.items():
            for event in user_events:
                if current_day in event['days'] and current_time in event['times']:
                    bot.send_message(chat_id, f"Напоминание! Событие '{event['name']}' сейчас.")
        time.sleep(60)


# Запуск бота и функции уведомлений
if __name__ == "__main__":
    from threading import Thread
    notification_thread = Thread(target=event_notification)
    notification_thread.start()
    bot.polling()
