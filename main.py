import telebot
import sqlite3
import os

from telebot import types, util

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

exercise=""
reps=""

# Reading workout data from files
monday_workout = open("large.txt", "rb").read()
wednesday_workout = open("shoulders.txt", "rb").read()
friday_workout = open('back.txt', "rb").read()

# Splitting workout data into chunks (Telegram message limit is 3000 characters)
splitted_monday = util.split_string(monday_workout, 3000)
splitted_wednesday = util.split_string(wednesday_workout, 3000)
splitted_friday = util.split_string(friday_workout, 3000)

# Handle /start command
@bot.message_handler(commands=['start'])
def start_handler(message):
    conn = sqlite3.connect('database.sql')
    curr = conn.cursor()
    curr.execute('CREATE TABLE IF NOT EXISTS fitness (id INTEGER PRIMARY KEY AUTOINCREMENT, exercise VARCHAR(50), reps VARCHAR(50), sets VARCHAR(50))')
    conn.commit()
    curr.close()
    conn.close()

    bot.send_message(message.chat.id, 'What exercise did you do?')
    bot.register_next_step_handler(message, exercise_name)

# Handle exercise name input
def exercise_name(message):
    global exercise
    exercise = message.text.strip()
    bot.send_message(message.chat.id, 'How many reps?')
    bot.register_next_step_handler(message, reps_input)

# Handle reps input
def reps_input(message):
    global reps
    reps = message.text.strip()
    bot.send_message(message.chat.id, 'How many sets?')
    bot.register_next_step_handler(message, sets_input)

# Handle sets input and save to database
def sets_input(message):
    sets = message.text.strip()

    conn = sqlite3.connect('database.sql')
    curr = conn.cursor()
    curr.execute("INSERT INTO fitness (exercise, reps, sets) VALUES (?, ?, ?)", (exercise, reps, sets))
    conn.commit()
    curr.close()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('Show results', callback_data='show_results'))
    bot.send_message(message.chat.id, 'Daily workout saved', reply_markup=markup)

# Handle /workout command
@bot.message_handler(commands=['workout'])
def workout_handler(message):
    markup = types.InlineKeyboardMarkup()
    monday_button = types.InlineKeyboardButton('Monday', callback_data='monday_workout')
    wednesday_button = types.InlineKeyboardButton('Wednesday', callback_data='wednesday_workout')
    friday_button = types.InlineKeyboardButton('Friday', callback_data='friday_workout')
    markup.row(monday_button, wednesday_button, friday_button)
    bot.send_message(message.chat.id, 'Choose a workout plan', reply_markup=markup)

# Callback query handler for workout plans
@bot.callback_query_handler(func=lambda call: True)
def workout_plan_handler(call):
    if call.data == 'monday_workout':
        for text in splitted_monday:
            bot.send_message(call.message.chat.id, text)
    elif call.data == 'wednesday_workout':
        for text in splitted_wednesday:
            bot.send_message(call.message.chat.id, text)
    elif call.data == 'friday_workout':
        for text in splitted_friday:
            bot.send_message(call.message.chat.id, text)

    # Here you can add more specific callback handling if needed, e.g., show_results
    elif call.data == 'show_results':
        conn = sqlite3.connect('database.sql')
        curr = conn.cursor()
        curr.execute('SELECT * FROM fitness')
        users = curr.fetchall()

        info = ''
        for el in users:
            info += f'Exercise: {el[1]}, Reps: {el[2]}, Sets: {el[3]}\n'

        bot.send_message(call.message.chat.id, info)
        curr.close()
        conn.close()

bot.polling()
